# 0002 — Selección de componentes del pipeline (VAD, turn detection, STT, LLM)

## Status

Accepted

## Context

Cada capa del pipeline de voz (VAD, detección de turno, STT, LLM) necesita un componente concreto, gratuito y capaz de correr autoalojado en un VPS sin GPU dedicada. Comparación completa de opciones por capa (incluyendo alternativas de pago descartadas por el no-negociable de costo cero) en `docs/02-componentes.md`.

## Decision

- **VAD:** Silero VAD (`silero.VAD.load()`) — liviano, CPU-only, ya integrado como plugin oficial de `livekit-agents`.
- **Turn detection:** `livekit.agents.inference.TurnDetector(version="v1-mini")` — corre localmente, sin costo, sin depender de un servicio externo de pago.
- **STT:** faster-whisper — implementación optimizada de Whisper para CPU, sin API keys, modelo descargable localmente.
- **LLM:** Ollama sirviendo `Qwen2.5-7B-Instruct` — servido vía el servicio Coolify `ollama-api` que ya corre en el VPS del usuario para otros proyectos (ver no-negociable #3 y ADR-0006 para la decisión de reutilización específica).

## Consequences

- El STT (faster-whisper) introduce un costo de recursos no trivial al arrancar (carga de modelo, posible descarga en frío) — esto motivó la tarea 4.2 en `docs/PLAN.md` (verificación vía `isolated-builder`) y el cambio de tamaño de modelo de `medium` (~1.5GB) a `small` (~500MB) documentado en esa misma tarea.
- El LLM depende de que el servicio `ollama-api` ya existente tenga el modelo `qwen2.5:7b-instruct` descargado — pendiente de confirmar (`docs/PLAN.md`, tarea 4.5).
- Todos estos componentes corren en CPU; el dimensionamiento de VPS (`docs/04-requisitos-vps.md`) asume CPU con soporte AVX2 como requisito duro para faster-whisper.
