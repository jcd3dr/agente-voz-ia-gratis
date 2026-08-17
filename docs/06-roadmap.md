# Roadmap del proyecto y de la serie de YouTube

> **Este documento es el roadmap histórico de la Etapa 1**, escrito antes de empezar el despliegue real. El **plan vivo y backlog actual** — con el estado real, tarea por tarea, de qué está hecho, en curso o bloqueado — está en [`../PLAN.md`](./PLAN.md). Ante cualquier discrepancia entre este documento y `docs/PLAN.md`, `docs/PLAN.md` manda. El contenido original de este archivo se conserva íntegro debajo como contexto histórico.

## Etapa 1 — Investigación y arquitectura (completada)

- Selección de framework de orquestación (LiveKit Agents)
- Selección de STT, LLM, TTS, VAD y turn detection 100% gratuitos y autoalojables
- Definición de requisitos de VPS
- Documentación honesta de la única excepción de gratuidad (telefonía PSTN)
- Definición del cliente de validación: landing page web mínima (ver [`07-cliente-web-landing.md`](./07-cliente-web-landing.md))

## Etapas 2 a 5 — código construido, pendiente de ejecutar en el VPS real

Todo el código de estas cuatro etapas ya está en el repositorio (carpetas `agent/`, `server/`, `piper/`, `docker/`, `web/`, `scripts/`), escrito y verificado contra el código fuente real de `livekit-agents==1.6.10` (clonado y revisado durante la construcción, no generado por analogía). Lo que falta es correrlo: este entorno de construcción no tenía acceso SSH al VPS ni a PyPI, así que el stack nunca se levantó de punta a punta contra un LiveKit Server real. Guía completa de despliegue: [`08-instalacion-despliegue.md`](./08-instalacion-despliegue.md).

### Etapa 2 — Preparación del VPS

- `scripts/01-setup-vps.sh`: instala Docker + plugin compose, verifica AVX2/RAM/disco, abre puertos en ufw
- `docker/Caddyfile`: dos subdominios con TLS automático (Let's Encrypt) — uno para LiveKit, otro para la landing page + servidor de tokens

### Etapa 3 — Despliegue de LiveKit Server + landing page mínima

- `docker/docker-compose.yml`: LiveKit Server + Redis
- `server/`: servidor de tokens (FastAPI + `livekit-api`, firma JWT sin exponer el secreto al navegador)
- `web/index.html`: landing page mínima (LiveKit Client SDK vía CDN, botón "Hablar con el agente")

### Etapa 4 — Instalación de componentes de IA

- Servicio `ollama` en `docker-compose.yml` (no expuesto al host) + `scripts/03-pull-ollama-model.sh`
- `agent/plugins/stt_faster_whisper.py`: STT local, modelo configurable vía `WHISPER_MODEL_SIZE`
- `piper/`: imagen Docker de Piper TTS (fork OHF-Voice/piper1-gpl, GPL-3.0-or-later — corrección de licencia respecto a la Etapa 1, ver [`02-componentes.md`](./02-componentes.md)) con descarga automática de la voz española en el primer arranque

### Etapa 5 — Construcción del agente (worker)

- `agent/agent.py`: `AgentSession` con VAD (Silero) → turn detector local (`inference.TurnDetector(version="v1-mini")`, corrección de API respecto a la Etapa 1) → STT (faster-whisper) → LLM (Ollama vía `openai.LLM.with_ollama`) → TTS (Piper por HTTP)
- Manejo de interrupciones: configuración por defecto de `TurnHandlingOptions`, sin overrides todavía

## Etapa 6 — Pruebas y ajuste de latencia (próximo paso real)

- Primera prueba de punta a punta en el VPS: seguir [`08-instalacion-despliegue.md`](./08-instalacion-despliegue.md) y hablar con el agente desde la landing page
- Medición de latencia real por etapa
- Tuning de parámetros (tamaño de modelo, streaming, buffers)
- Corregir en el código cualquier desajuste entre lo verificado contra el SDK y su comportamiento real bajo carga

## Etapa 7 — Demo pública y cierre de la serie

- Pulido de la landing page (indicadores de estado: escuchando/pensando/hablando)
- Grabación de la demo final para el video de cierre

---

Cada etapa corresponde a un video/capítulo separado de la serie.

---

**Nota (2026-08-17):** desde que se escribió este roadmap, la Etapa 6 pasó de "TTS=Piper" a "TTS=Kokoro-FastAPI reutilizado" (ver [`docs/adr/0004-*.md`](./adr/0004-tts-kokoro-fastapi-supersede-piper.md)) y el despliegue se está haciendo vía Coolify en vez de únicamente SSH manual (ver [`docs/adr/0006-*.md`](./adr/0006-despliegue-coolify-nativo.md)). El detalle vivo de qué está hecho y qué falta de la Etapa 6 real está en [`../PLAN.md`](./PLAN.md), Fase 4.
