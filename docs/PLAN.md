# PLAN.md — Plan vivo y backlog

Este es el **único** plan vivo del proyecto. Leer `AGENTS.md` primero (cómo se trabaja), después este archivo completo (qué falta y en qué estado), y los ADRs en `docs/adr/` solo si la tarea toca algo con historia de decisiones.

Los documentos `docs/01-*.md` a `docs/08-*.md` son investigación/especificación histórica de la Etapa 1 — útiles como contexto, pero **no se actualizan como plan vivo**. Si algo de ahí queda obsoleto por una decisión posterior, esa decisión vive en un ADR y (si aplica) se referencia aquí, no se edita el doc histórico.

Vocabulario de estado (fijo, no inventar variantes):
`TODO` · `IN_PROGRESS` · `BLOCKED: <razón>` · `DONE` · `SUPERSEDED: <por qué / por qué tarea>` · `ABANDONED: <por qué>`

---

## Estado actual

- **Fecha última actualización:** 2026-08-17
- **Agente que actualizó:** Claude (Claude Code / Cowork, sesión de despliegue Coolify + reestructuración multi-agente)
- **Fase activa:** Fase 4 — Despliegue en Coolify (ver backlog abajo). La Fase 5 (reestructuración multi-agente: `AGENTS.md` + este archivo + `docs/adr/`) queda completa y pusheada a `main` con esta misma actualización.
- **Tarea en curso:** Ninguna en ejecución activa en este momento. La próxima tarea a retomar es **4.1** (LiveKit no arranca en el VPS), estado `BLOCKED` — ver nota de handoff en esa tarea, es el punto de reanudación más importante para la próxima sesión.
- **Último bloqueo:** LiveKit Server no llega a estado healthy en el Service de Coolify `voz-ia-infra`, con tres configuraciones distintas probadas (todas fallaron igual, incluyendo el modo cero-config `--dev` de LiveKit). Hipótesis líder no confirmada: agotamiento de memoria del VPS (~15+ servicios corriendo en el mismo host). Sin herramienta de métricas de RAM disponible vía `coolify-mcp`. El servicio Coolify que se estaba probando (`vfuz5azxdz2keib3vifqhjoh`, nombre "voz-ia-infra") **fue eliminado** al final de la sesión anterior para dejar de estresar el VPS — no existe ahora mismo ningún recurso "voz-ia-infra" en Coolify; hay que recrearlo desde cero.
- **Nota importante de contexto:** en esta misma sesión se generaron credenciales reales de LiveKit (API key + secret) para probar el despliegue. **No están escritas en ningún archivo de este repo** (por no-negociable #4 de `AGENTS.md`) y no sobrevivieron a la eliminación del servicio de Coolify. Si se recrea el servicio, hay que generar credenciales nuevas.

---

## Backlog

### Fase 1 — Investigación y diseño (Etapa 1 histórica)

**1.1 — Elección de framework de orquestación**
- Estado: `DONE`
- Contexto: evaluar frameworks de agentes de voz open source antes de comprometerse a uno.
- Evidencia: comparación completa en `docs/03-alternativas-frameworks.md`. Decisión registrada en `docs/adr/0001-livekit-agents-como-orquestador.md`.

**1.2 — Selección de componentes del pipeline (VAD, turn detection, STT, LLM)**
- Estado: `DONE`
- Contexto: elegir un componente concreto y gratuito por cada capa del pipeline de voz.
- Evidencia: tablas comparativas en `docs/02-componentes.md`. Decisión registrada en `docs/adr/0002-seleccion-componentes-pipeline.md`.

**1.3 — Selección inicial de TTS (Piper)**
- Estado: `SUPERSEDED: por la tarea 3.2 (migración a Kokoro-FastAPI, ver ADR-0004)`
- Contexto: elección original de TTS. Registrada en `docs/adr/0003-tts-piper.md`, incluye la corrección de licencia (GPL-3.0-or-later, no MIT como se asumió al principio).

**1.4 — Requisitos de VPS**
- Estado: `DONE`
- Contexto: dimensionar el VPS necesario (CPU con AVX2, RAM, disco) para correr el pipeline completo.
- Evidencia: `docs/04-requisitos-vps.md` (tablas de sizing, sección "Plan B" con Groq documentado como fallback no-autoalojado, no adoptado).

**1.5 — Alcance de telefonía (PSTN)**
- Estado: `DONE` (como decisión de alcance, no como feature implementada)
- Contexto: decidir si telefonía real (PSTN) entra en alcance. Se documentó como fuera de alcance porque no es gratis (única excepción documentada al no-negociable #1 de costo cero).
- Evidencia: `docs/05-telefonia-sip.md`.

**1.6 — Cliente web de validación (landing)**
- Estado: `DONE`
- Contexto: decidir cómo se prueba el agente en v1 sin construir una app completa.
- Evidencia: `docs/07-cliente-web-landing.md`, implementado en `web/index.html`.

### Fase 2 — Implementación del agente

**2.1 — Worker de LiveKit Agents (pipeline completo)**
- Estado: `DONE`
- Contexto: implementar `agent/agent.py` con VAD (Silero) + turn detection (`inference.TurnDetector v1-mini`) + STT (faster-whisper) + LLM (Ollama) + TTS.
- Criterios de aceptación: el agente instancia todas las piezas sin error de import/config; verificado por separado en Fase 4 (isolated-builder) para las piezas más pesadas.
- Archivos: `agent/agent.py`, `agent/plugins/`.
- Evidencia: código presente y coherente con `livekit-agents==1.6.10` (verificado contra fuente real, ver comentarios en el propio código). No probado contra un LiveKit Server real corriendo (eso es exactamente la tarea 4.1, bloqueada).

**2.2 — Servidor de tokens**
- Estado: `DONE`
- Contexto: la landing page necesita un backend que emita tokens de LiveKit sin exponer el API secret al navegador.
- Archivos: `server/` (FastAPI + `livekit-api`).
- Evidencia: código presente, no desplegado aún como Application de Coolify (eso es tarea 4.3).

**2.3 — Landing page de validación**
- Estado: `DONE`
- Archivos: `web/index.html`.
- Evidencia: implementado y actualizado en esta sesión para apuntar a `TOKEN_SERVER_URL` absoluto (`https://agente-voz-token.jcdcruz.com/token`) en vez de un fetch relativo `/token`, porque landing y token-server se van a desplegar como dos Applications de Coolify separadas con dominios distintos. Commit `d5142db`.

### Fase 3 — Corrección TTS (Piper → Kokoro-FastAPI)

**3.1 — Diagnóstico: por qué no usar el plugin oficial `openai.TTS` contra Kokoro-FastAPI**
- Estado: `DONE`
- Contexto: Kokoro-FastAPI expone una API compatible con OpenAI, pero `livekit-plugins-openai` usa `SSEChunkedStream` (protocolo de eventos `speech.audio.delta`) para cualquier modelo que no sea `tts-1`/`tts-1-hd`, y Kokoro no confirma soportar ese protocolo SSE.
- Evidencia: verificado leyendo el código fuente real de `livekit-plugins-openai` (`AUDIO_STREAM_MODELS = {"tts-1", "tts-1-hd"}`).

**3.2 — Implementar plugin HTTP batch custom para Kokoro-FastAPI**
- Estado: `DONE`
- Contexto: en vez de arriesgar el mismatch de protocolo, se escribió un plugin propio (`tts.ChunkedStream`) que llama `POST /v1/audio/speech` con `response_format=wav` y decodifica localmente, igual que el patrón ya usado para Piper.
- Archivos: `agent/plugins/tts_kokoro_http.py` (nuevo), `agent/agent.py` (import + `KOKORO_BASE_URL`/`KOKORO_VOICE` env vars), `agent/requirements.txt` (comentario actualizado).
- Evidencia: commit `d5142db`. Reutiliza el servicio Coolify `kokoro-tts` ya corriendo (no-negociable #3) en vez de desplegar un Piper/Kokoro nuevo.
- Decisión registrada en `docs/adr/0004-tts-kokoro-fastapi-supersede-piper.md`.

**3.3 — Actualizar README.md y docs con la elección de TTS vigente**
- Estado: `DONE`
- Contexto: `README.md` todavía listaba Piper como elección de TTS en su tabla de stack — quedó desactualizado por la tarea 3.2.
- Evidencia: tabla de stack de `README.md` actualizada (Kokoro-FastAPI, con link a `docs/adr/0004-*.md` en vez de detalle inline), incluida en el mismo commit que el resto de la Fase 5 (ver 5.5).
- Archivos: `README.md`.

### Fase 4 — Despliegue en Coolify

**4.1 — LiveKit Server no arranca en el VPS (Service `voz-ia-infra`)**
- Estado: `BLOCKED: causa raíz no confirmada, hipótesis líder = agotamiento de RAM del VPS, sin herramienta de métricas de memoria disponible vía coolify-mcp`
- Contexto: se necesita un LiveKit Server corriendo en el VPS (junto con Redis) para que el agent worker y la landing page tengan a qué conectarse. Se creó un Service de Coolify con `redis` + `livekit` (+ un contenedor one-shot `pull-model` para descargar el modelo de Ollama) llamado "voz-ia-infra".
- **Lo que se probó y descartó como causa:**
  - El **build de la imagen del agente** NO es la causa: descartado mediante un run real y exitoso en `jcd3dr/isolated-builder` (ver tarea 4.2, `DONE`). Imagen construye en ~80s, faster-whisper "small" carga y pasa health check en ~4s, sin anomalías.
  - **No es un error de configuración de LiveKit Server**: se probaron tres variantes de config para el contenedor `livekit` — (a) `LIVEKIT_CONFIG` con YAML completo, (b) variables de entorno planas (`LIVEKIT_KEYS`, `REDIS_HOST`, etc.), (c) modo cero-config oficial `--dev` — las tres fallaron de forma idéntica. Esto descarta un typo o mecanismo de config incorrecto, porque hasta el modo `--dev` (sin ninguna config custom) falló igual.
  - Verificado contra el código fuente real de `livekit/livekit` (Go) que `LIVEKIT_CONFIG`, `LIVEKIT_KEYS` (formato exacto `key: secret`, con el espacio), `REDIS_HOST`/`REDIS_PASSWORD` son mecanismos reales y válidos — no es un problema de estar usando variables de entorno inventadas.
- **Lo que NO se pudo verificar** (por falta de herramienta, no por decisión): uso real de RAM del VPS en el momento de los fallos. `mcp__coolify-mcp__server_resources` fue explorado pero no expone memoria; no hay acceso SSH directo desde esta sesión.
- **Nota de handoff (obligatoria, para la próxima sesión/agente):**
  - Estado real del código: no hace falta cambiar nada en este repo para retomar esta tarea — el problema es 100% de infraestructura Coolify/VPS, no del código de `agent/`, `server/` o `docker/`.
  - El servicio de Coolify de la prueba anterior (`vfuz5azxdz2keib3vifqhjoh`, "voz-ia-infra") **ya no existe** — fue borrado (`delete_volumes=true`) para dejar de estresar el VPS. Hay que recrearlo desde cero si se retoma esta vía.
  - **Próximo paso concreto:** antes de recrear el servicio, confirmar memoria libre real del VPS. Opciones: (a) pedir al usuario que corra `free -h` por SSH y reporte el resultado, o (b) revisar los gráficos de recursos en la UI de Coolify (Server → Resources), ninguna de las dos accesible desde `coolify-mcp` en el momento de escribir esto. Si la RAM libre es baja (<1-2GB libres con ~15+ servicios corriendo), la hipótesis de agotamiento de memoria queda confirmada y la solución es: reducir el footprint del Service `voz-ia-infra` (¿LiveKit Server realmente necesita Redis para un solo nodo? — verificar en `livekit/livekit` docs/código si Redis es opcional en modo single-node antes de asumir que hace falta) o mover LiveKit Server a un plan/VPS con más RAM.
  - Si la RAM no es el problema, siguiente hipótesis a probar: revisar el log real del contenedor `livekit` con `mcp__coolify-mcp__logs(resource=service, uuid=<nuevo-uuid>, container=livekit)` — en esta sesión ese comando resultó no confiable/colgó repetidamente para el contenedor `livekit` específicamente (sí funcionó para otros contenedores), lo cual es en sí mismo una pista no explorada (¿el contenedor no llega a emitir logs porque muere antes de inicializar el logger, o es un problema del propio `coolify-mcp` con ese contenedor? — no determinado).
  - Comando exacto para recrear el servicio: `mcp__coolify-mcp__service(action=create, ...)` con un `docker_compose_raw` que incluya `redis` + `livekit` — ver el compose usado en los tres intentos anteriores (no versionado en este repo porque contenía credenciales generadas; si se retoma, generar credenciales nuevas con `python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(32)))"` o equivalente, y NO escribirlas en ningún archivo de este repo).
  - Decisión de arquitectura relacionada (topología de dos subdominios, red interna) registrada en `docs/adr/0005-topologia-dos-subdominios.md`.

**4.2 — Verificar build/arranque de la imagen del agente sin tocar el VPS (isolated-builder)**
- Estado: `DONE`
- Contexto: antes de intentar desplegar en el VPS de producción, descartar que la imagen Docker del agente sea la causa de cualquier fallo, usando el repo público `jcd3dr/isolated-builder` (GitHub Actions, runners efímeros).
- Criterios de aceptación: un run de GitHub Actions completa exitosamente el build + arranque + health check de `docker/smoketest-agent-compose.yml`.
- Evidencia real: run exitoso en https://github.com/jcd3dr/isolated-builder/actions/runs/31997239848 — imagen construida en ~80s, modelo faster-whisper "small" cargado y health check respondido en ~4s, sin anomalías de recursos observadas en el runner.
- Archivos: `agent/smoketest.py` (nuevo), `docker/smoketest-agent-compose.yml` (nuevo). Commit `d5142db`.
- Cambio relacionado que motivó parte de este trabajo: `WHISPER_MODEL_SIZE` default cambiado de `"medium"` (~1.5GB de descarga) a `"small"` (~500MB) en `agent/agent.py`, más `WHISPER_DOWNLOAD_ROOT` configurable para poder cachear el modelo entre reinicios del contenedor (evita una descarga bloqueante de ~1.5GB en cada arranque en frío — identificado como un defecto real y corregible, aunque no confirmado como la causa del crash original del VPS).

**4.3 — Desplegar `token-server`, `agent` worker y `web` como Applications de Coolify**
- Estado: `TODO`
- Contexto: una vez que 4.1 esté resuelto (LiveKit Server sano), desplegar las tres piezas restantes como Applications de Coolify (build desde GitHub, este repo).
- Criterios de aceptación: los tres servicios corren y quedan healthy; la landing page (`https://agente-voz.jcdcruz.com`) consigue un token del token-server (`https://agente-voz-token.jcdcruz.com`) y el agent worker se une a una sala real.
- Dependencias: 4.1 (LiveKit Server sano), resolución de la tarea 4.4 (networking interno).
- Parámetros ya decididos (de la sesión de diseño previa, no ejecutados aún): token-server con `base_directory=/server`, `fqdn=https://agente-voz-token.jcdcruz.com`, puerto 8080; landing con `base_directory=/web`, `fqdn=https://agente-voz.jcdcruz.com`; agent worker con `base_directory=/agent`, sin `fqdn` (no expuesto por HTTP).

**4.4 — Networking interno: agent worker → `ollama-api` / `kokoro-tts`**
- Estado: `TODO`
- Contexto: el agent worker (Application de Coolify) necesita alcanzar por red interna los servicios `ollama-api` y `kokoro-tts`, que ya corren como Services separados de Coolify en el mismo VPS (no-negociable #3 — reutilizar, no duplicar).
- Lo que se sabe (verificado vía `search_docs`/`WebFetch` contra la documentación real de Coolify, no probado end-to-end): cada Service de Coolify corre en su propia red Docker privada nombrada literalmente por el UUID del recurso Service. El toggle "Connect to Predefined Network" (solo UI, no expuesto por `coolify-mcp`) es el mecanismo oficialmente soportado para unir una Application a la red compartida `coolify`. Declarar redes externas custom manualmente en una Application tipo "Docker Compose" está explícitamente desaconsejado por la documentación de Coolify (riesgo de 504 por aislamiento del proxy Traefik) — pero esa advertencia es específica de servicios expuestos por FQDN/proxy, no necesariamente aplica al agent worker (que no tiene `fqdn`, no pasa por Traefik).
- **No confirmado:** si declarar la red externa del Service `ollama-api`/`kokoro-tts` directamente en el compose del agent worker (semántica estándar de Docker Compose) funciona en la práctica en este VPS. Se probó una vez con éxito para un contenedor de bajo riesgo (`pull-model`, one-shot) en un intento de despliegue anterior, pero ese Service completo fue borrado antes de poder validar el caso real (agent worker persistente).
- Próximo paso concreto: una vez 4.1 esté resuelto y haya un Service "voz-ia-infra" vivo de nuevo, crear el agent worker Application con `custom_docker_run_options`/red externa apuntando a los nombres de red UUID reales de `ollama-api` y `kokoro-tts` (consultar `mcp__coolify-mcp__get_service`/`list_services` para obtener esos UUIDs exactos, cambian por instalación), y confirmar con un log real de conexión exitosa (no asumir).

**4.5 — Pull del modelo `qwen2.5:7b-instruct` en el `ollama-api` ya existente**
- Estado: `TODO`
- Contexto: el LLM del pipeline depende de que ese modelo específico esté descargado en el servicio `ollama-api` ya vivo en el VPS. No confirmado si ya está descargado de un uso anterior de ese servicio para otro proyecto.
- Próximo paso concreto: verificar primero con `ollama list` (vía exec en el contenedor, o el endpoint HTTP de Ollama) si el modelo ya existe antes de asumir que hace falta descargarlo.

### Fase 5 — Reestructuración multi-agente (esta tarea, en curso)

**5.1 — Auditoría de contenido existente**
- Estado: `DONE`
- Contexto: antes de crear `AGENTS.md`/`docs/PLAN.md`/`docs/adr/`, revisar todo el contexto disperso existente (README, docs 01-08, historial de commits, issues) para no perder ni duplicar nada.
- Evidencia: `README.md`, los 8 archivos `docs/0N-*.md`, historial completo de 7 commits (todos auto-autoría dentro de este mismo proyecto, sin contribuciones externas) revisados vía `get_file_contents`/`list_commits`. `list_issues` devolvió `503` transitorio dos veces — no bloqueante dado que el historial de commits confirma que no hay colaboradores externos ni issues previos relevantes, pero queda anotado aquí honestamente como un hueco de auditoría no resuelto, no como "cero issues confirmado".

**5.2 — Escribir `AGENTS.md`**
- Estado: `DONE`
- Contexto: constitución del proyecto — stack, no-negociables, convenciones, protocolo de trabajo multi-agente.
- Archivos: `AGENTS.md` (raíz del repo).
- Evidencia: archivo escrito y pusheado en el mismo commit que el resto de la Fase 5.

**5.3 — Escribir `docs/PLAN.md`**
- Estado: `DONE`
- Contexto: este mismo archivo.

**5.4 — Escribir `docs/adr/README.md` + ADRs 0001-0006**
- Estado: `DONE`
- Contexto: migradas las decisiones ya tomadas (dispersas en `docs/01-*.md` a `docs/08-*.md`) al formato ADR estándar, más registrada como ADR nueva la decisión de Kokoro-FastAPI (que nunca se había documentado formalmente como decisión, solo como cambio de código).
- Archivos creados: `docs/adr/README.md`, `docs/adr/0001-livekit-agents-como-orquestador.md`, `docs/adr/0002-seleccion-componentes-pipeline.md`, `docs/adr/0003-tts-piper.md` (con `Status: Superseded by ADR-0004`), `docs/adr/0004-tts-kokoro-fastapi-supersede-piper.md`, `docs/adr/0005-topologia-dos-subdominios.md`, `docs/adr/0006-despliegue-coolify-nativo.md`.

**5.5 — Push de `AGENTS.md` + `docs/PLAN.md` + `docs/adr/*` a GitHub**
- Estado: `DONE`
- Contexto: hasta que estos archivos no estuvieran en `main`, ninguna otra sesión/agente podía usarlos — era el paso que hacía real el objetivo de esta fase.
- Evidencia: commit único en `main` de `jcd3dr/agente-voz-ia-gratis` con los 11 archivos de esta fase (`AGENTS.md`, `docs/PLAN.md`, `docs/adr/README.md` + 6 ADRs, `README.md`, `docs/06-roadmap.md`) vía `mcp__github-mcp__push_files`. Ver SHA del commit en el historial de git (`git log`/`list_commits`) — no repetido aquí para no quedar obsoleto si hay commits posteriores.

**5.6 — Actualizar `README.md` y `docs/06-roadmap.md` con punteros a la nueva estructura**
- Estado: `DONE`
- Contexto: `README.md` y `docs/06-roadmap.md` señalan ahora `AGENTS.md`/`docs/PLAN.md` como la fuente de verdad viva, sin borrar su contenido histórico (`docs/06-roadmap.md` conserva íntegro el roadmap original Etapa 1-7, con una nota final apuntando a `docs/PLAN.md`).
- Evidencia: banner al inicio de ambos archivos, contenido original intacto debajo. Incluido en el mismo commit que 5.5. Combinada con 3.3 (tabla de stack de `README.md`) en el mismo archivo/commit.
