# 0001 — LiveKit Agents + LiveKit Server como orquestador/transporte

## Status

Accepted

## Context

El proyecto necesita un framework que maneje: transporte de audio en tiempo real (WebRTC), orquestación del pipeline de voz (VAD → turn detection → STT → LLM → TTS, con interrupciones/barge-in), y que permita usar componentes 100% open source y autoalojados sin depender de APIs de pago.

Se evaluaron alternativas open source para agentes de voz: LiveKit Agents, Pipecat, TEN, Bolna, Vocode, FastRTC. Comparación completa (features, madurez, soporte de self-hosting, comunidad, facilidad de integrar componentes custom) en `docs/03-alternativas-frameworks.md`.

## Decision

Usar **LiveKit Agents SDK** (Python, worker de agente) + **LiveKit Server** (Go, self-hosted, sin usar LiveKit Cloud) como orquestador y transporte de audio.

Versión verificada contra código fuente real al momento de esta decisión: `livekit-agents==1.6.10`. Cualquier uso de una API de esta librería que no esté ya presente en el repo debe re-verificarse contra el código fuente clonado si cambia la versión (ver `AGENTS.md`, sección "Cómo verificar").

## Consequences

- LiveKit Server debe autoalojarse en el VPS propio (Coolify) — no se usa LiveKit Cloud, por el no-negociable de costo cero recurrente.
- El proyecto queda acoplado a la API y convenciones de LiveKit Agents (`AgentServer`, `@server.rtc_session()`, `AgentSession`, `TurnHandlingOptions`) — ver `agent/agent.py`.
- El despliegue del LiveKit Server self-hosted es no trivial (requiere Redis para modo distribuido, configuración de keys, networking) — esto es precisamente la causa del bloqueo documentado en `docs/PLAN.md`, tarea 4.1, al momento de escribir este ADR.
- Ganamos: SDK maduro con soporte first-class para VAD/turn-detection/plugins intercambiables, lo cual permitió construir plugins custom (`agent/plugins/tts_kokoro_http.py`) verificando contra la interfaz real (`tts.TTS`/`tts.ChunkedStream`) en vez de estar atado a integraciones oficiales limitadas.
