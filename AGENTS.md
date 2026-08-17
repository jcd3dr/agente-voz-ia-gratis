# AGENTS.md — Constitución del proyecto

Este archivo es la fuente de verdad de **cómo** se trabaja en este repo. Cambia poco. Cualquier agente (Claude, Codex CLI, Antigravity/agy, Copilot, Cursor, u otro) que abra este repo sin memoria de sesiones anteriores debe leer **este archivo primero**, y después `docs/PLAN.md`, antes de tocar código.

Para **qué** se está construyendo y **por qué**, y en qué punto está ahora mismo: ver `docs/PLAN.md` (plan vivo y backlog) y `docs/adr/` (decisiones técnicas). Este archivo no repite ese contenido.

## Qué es este proyecto

Un agente conversacional de voz (STT → LLM → TTS en tiempo real, streaming, interrumpible) construido exclusivamente con componentes open source, autoalojado en un VPS propio, sin API keys de pago. Es el material de referencia de una serie de YouTube que documenta la construcción completa desde cero — el código y la documentación son en sí mismos el contenido del video, no solo un medio para llegar a un producto.

## Stack técnico (qué es, no por qué — el porqué está en `docs/adr/`)

| Capa | Componente | Dónde vive en el repo |
|---|---|---|
| Orquestador / transporte de audio | LiveKit Agents (worker) + LiveKit Server | `agent/`, infra Coolify "voz-ia-infra" |
| VAD | Silero VAD | `agent/agent.py` (`silero.VAD.load()`) |
| Turn detection | `livekit.agents.inference.TurnDetector(version="v1-mini")` | `agent/agent.py` |
| STT | faster-whisper | `agent/plugins/stt_faster_whisper.py` |
| LLM | Ollama + Qwen2.5-7B-Instruct (servicio Coolify `ollama-api`, ya existente, reutilizado) | `agent/agent.py` (`openai.LLM.with_ollama`) |
| TTS | Kokoro-FastAPI (servicio Coolify `kokoro-tts`, ya existente, reutilizado) | `agent/plugins/tts_kokoro_http.py` |
| Servidor de tokens | FastAPI + `livekit-api` | `server/` |
| Cliente de validación v1 | Landing page HTML + LiveKit Client SDK | `web/` |
| Despliegue | Coolify (PaaS self-hosted que ya administra el VPS) — Services (docker-compose) y Applications (build desde este repo vía GitHub) | Ver `docs/adr/0006-*.md` |

Versión exacta de `livekit-agents` verificada contra código fuente real: `1.6.10`. No asumir APIs de versiones distintas sin re-verificar contra el código fuente clonado (ver sección "Cómo verificar" abajo).

## No-negociables

1. **Cero costo recurrente.** Ningún componente puede requerir una API key de pago (OpenAI, ElevenLabs, Deepgram, LiveKit Cloud, etc.). Excepción documentada y explícita: telefonía PSTN real, fuera de alcance actual (ver `docs/adr/` si en el futuro se agrega — hoy no existe ese ADR porque no se ha implementado).
2. **Self-hosted por defecto.** Antes de agregar cualquier servicio en la nube (incluso con capa gratuita), evaluar primero si cabe autoalojado en el VPS. Un componente en la nube es la excepción, no el default, y requiere su propio ADR explicando el trade-off.
3. **No duplicar infraestructura ya viva en el VPS.** El VPS (gestionado por Coolify) ya corre `ollama-api` y `kokoro-tts` para otros proyectos del dueño del repo. Este proyecto los reutiliza — no despliega su propio Ollama ni su propio Piper/TTS redundante. Antes de crear un recurso nuevo en Coolify, comprobar si ya existe algo reutilizable (`mcp__coolify-mcp__list_services` / `list_applications`).
4. **Nunca commitear secretos reales.** Placeholders y `.env.example` sí; `.env` real, API keys, o secretos de LiveKit generados para despliegues reales, no — ni en código, ni en `docs/PLAN.md`, ni en ADRs. Este repo es **público**. Si un secreto ya fue generado para un despliegue real, se referencia por nombre de variable/mecanismo, nunca por valor, en cualquier archivo versionado.
5. **No confabular verificación.** Nada se documenta como "funciona" o "DONE" sin evidencia real de haberlo ejecutado (comando corrido + output observado, o un link a un run de CI/Actions). "Debería funcionar" no es DONE — ver vocabulario de estado en `docs/PLAN.md`.

## Convenciones

- **Idioma:** documentación y comentarios de código en español (es el idioma del video/audiencia). Nombres de variables/funciones en inglés (convención estándar de código). Mensajes de commit en español.
- **Verificación contra fuente real, no memoria del modelo:** cualquier API de `livekit-agents`, `livekit-api`, plugins oficiales, o de LiveKit Server (Go) que no esté ya usada en este repo debe verificarse clonando el repo fuente real (`livekit/agents`, `livekit/python-sdks`, `livekit/livekit`) y leyendo el código, no generarse por analogía o recuerdo de entrenamiento. Cuando eso ya se hizo para algo, queda anotado en el ADR o el código correspondiente — no repetir la verificación si ya está documentada, pero si se toca esa pieza, revalidar que sigue vigente en la versión actual.
- **Testing de imágenes Docker sin tocar el VPS de producción:** usar el repo público `jcd3dr/isolated-builder` (GitHub Actions, runners efímeros gratuitos) para construir/arrancar imágenes antes de desplegarlas en Coolify. Ver su propio `README.md` para el protocolo de disparo (`workflow_dispatch` con `target_repo=jcd3dr/agente-voz-ia-gratis`). Esto existe específicamente porque el entorno de desarrollo típico de un agente CLI no tiene Docker corriendo, y porque el VPS de producción no debe usarse para descartar errores de construcción.
- **Python:** 3.11 (ver `agent/Dockerfile`, `server/Dockerfile`). Sin virtualenv en contenedores (pip directo).
- **Licencias por componente:** verificar y anotar la licencia real de cualquier dependencia nueva antes de adoptarla (ver precedente: Piper resultó GPL-3.0-or-later, no MIT como se asumió inicialmente — `docs/adr/0003-tts-piper.md`). Copyleft (GPL) es aceptable si el componente se consume como servicio HTTP externo, no si se enlaza/modifica su código dentro de este repo.

## Protocolo de trabajo multi-agente (obligatorio, sin excepciones)

Este proyecto está diseñado para sobrevivir el agotamiento de contexto/créditos de cualquier sesión y continuar desde cualquier agente CLI. Para cada pedido:

1. **Antes de escribir código:** leer este archivo completo y `docs/PLAN.md` completo. Si el pedido toca algo con historia de decisiones (arquitectura, elección de componente, topología de red, despliegue), leer también los ADRs relevantes en `docs/adr/` (el índice en `docs/adr/README.md` ayuda a ubicar cuál).
2. **Ubicar o crear la tarea** correspondiente en el backlog de `docs/PLAN.md`. Si no existe, crearla ahí desglosada en subtareas concretas antes de ejecutar nada.
3. **Ejecutar el pedido.**
4. **Antes de terminar el turno**, sin excepción:
   - Actualizar el bloque "Estado actual" y el backlog de `docs/PLAN.md` reflejando exactamente qué cambió y qué falta.
   - Si quedó algo sin terminar, escribir la nota de handoff con precisión obligatoria (ver formato en `docs/PLAN.md`): qué es cierto ya en el código, próximo paso concreto, archivo/línea, comando exacto a correr.
   - Si se tomó una decisión técnica significativa y difícil de revertir, escribir un ADR nuevo en `docs/adr/` (no describirla solo en el chat o el mensaje de commit — el chat no sobrevive a la sesión).
   - Si una decisión anterior quedó obsoleta, el ADR que la registró se marca `Status: Superseded by ADR-00NN` (no se edita ni se borra) y se crea el ADR nuevo.
5. **Nunca dejar `docs/PLAN.md` desactualizado** respecto al estado real del código al cerrar una sesión — es el único mecanismo de continuidad entre agentes que no comparten memoria.

## Agnosticismo de herramienta

No asumir que la siguiente sesión tiene:
- Memoria de esta conversación (no la tiene, por diseño).
- El mismo conector MCP configurado (ej. `coolify-mcp`) — si se usó uno, documentar en `docs/PLAN.md` o el ADR correspondiente el nombre del servicio/herramienta usada y qué hace, no solo el nombre interno de la tool call.
- Acceso a Docker local — ver la sección de `isolated-builder` arriba.
- Contexto de un sistema externo (paneles, dashboards, bases de conocimiento) sin que el repo diga explícitamente dónde consultarlo. Si algo vive fuera del repo (ej. estado real de recursos en Coolify, un secreto generado), `docs/PLAN.md` debe decir *cómo* consultarlo (qué panel, qué comando, qué UUID/nombre de recurso), no asumir que se sabe.

## Cómo verificar antes de codificar contra un SDK

1. Clonar el repo fuente real (`git clone --depth 1 <repo>`), no confiar en memoria de entrenamiento.
2. Leer el código real de la clase/función que se va a usar.
3. Anotar en un comentario del código nuevo qué se verificó y contra qué versión/commit, siguiendo el patrón ya usado en `agent/agent.py` y `agent/plugins/*.py`.

## Estructura del repositorio

```
AGENTS.md              — este archivo (constitución)
docs/PLAN.md            — plan vivo y backlog (leer después de este archivo)
docs/adr/                — decisiones técnicas (Architecture Decision Records)
docs/01-08-*.md          — investigación y especificaciones de la Etapa 1 (contexto histórico, no plan vivo)
agent/                  — worker LiveKit Agents: VAD + turn detection + STT (faster-whisper) + LLM (Ollama) + TTS (Kokoro-FastAPI)
server/                 — servidor de tokens LiveKit (FastAPI) para la landing page
piper/                  — imagen Docker de Piper TTS — SUPERSEDED, ver docs/adr/0004-*.md, no se usa en el despliegue actual
docker/                 — docker-compose.yml y config de referencia (despliegue manual alternativo) + docker/smoketest-agent-compose.yml (para isolated-builder)
web/                    — landing page mínima de validación (LiveKit Client SDK)
scripts/                — setup de VPS por SSH manual (alternativa a Coolify, ver docs/adr/0006-*.md)
```
