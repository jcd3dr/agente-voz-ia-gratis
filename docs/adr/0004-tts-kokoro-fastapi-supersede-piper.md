# 0004 — TTS: Kokoro-FastAPI (reemplaza Piper)

## Status

Accepted (supersedes ADR-0003)

## Context

Durante el trabajo de despliegue en Coolify se confirmó que el VPS del usuario ya corre un servicio **Kokoro-FastAPI** (`ghcr.io/remsky/kokoro-fastapi-cpu`, nombre de servicio Coolify `kokoro-tts`) para otro proyecto del dueño del repo — igual que `ollama-api` para el LLM. El no-negociable #3 de `AGENTS.md` ("no duplicar infraestructura ya viva en el VPS") hace que reutilizar este servicio sea preferible a mantener el Piper dedicado descrito en ADR-0003.

Kokoro-FastAPI expone un endpoint compatible con la API de OpenAI (`POST /v1/audio/speech`), lo cual planteó la pregunta de si se podía usar directamente el plugin oficial `livekit-plugins-openai` en vez de escribir uno custom.

Se verificó leyendo el código fuente real de `livekit-plugins-openai` (clase `TTS`/`ChunkedStream` en `tts.py`) que ese plugin decide el protocolo de streaming según el nombre del modelo: `AUDIO_STREAM_MODELS = {"tts-1", "tts-1-hd"}` usa `AudioChunkedStream` (bytes de audio completos), pero **cualquier otro nombre de modelo** (incluyendo el default `gpt-4o-mini-tts` y, por extensión, cualquier nombre custom como `"kokoro"`) usa `SSEChunkedStream`, que parsea el protocolo de eventos SSE más nuevo de OpenAI (`speech.audio.delta`). No hay confirmación de que Kokoro-FastAPI implemente ese protocolo SSE — forzar el plugin oficial con `model="tts-1"` para evitar el SSE dependería de que Kokoro ignore silenciosamente ese nombre de modelo, lo cual no está documentado ni verificado.

## Decision

En vez de arriesgar el plugin oficial contra un protocolo no verificado, se implementó un **plugin HTTP batch propio**: `agent/plugins/tts_kokoro_http.py`, siguiendo el mismo patrón ya usado y verificado para Piper (`tts_piper_http.py`) — implementa directamente la interfaz `tts.TTS`/`tts.ChunkedStream` de `livekit-agents`, hace `POST {base_url}/v1/audio/speech` con `response_format=wav`, y deja que `AudioEmitter`/`AudioStreamDecoder` de `livekit-agents` decodifiquen y remuestreen el WAV recibido — confirmado por lectura del código fuente real que el `sample_rate` declarado en `initialize()` es un target de remuestreo, no un valor que deba coincidir exactamente con el sample rate nativo real de Kokoro (que no está documentado oficialmente).

`agent/agent.py` se actualizó para usar `KokoroTTS(base_url=KOKORO_BASE_URL, voice=KOKORO_VOICE)` con defaults `http://kokoro-tts:8880` / `ef_dora` (voz en español, prefijo `ef_`, confirmado en el README real del proyecto Kokoro-FastAPI vía fetch directo el 2026-08-17).

## Consequences

- Se elimina la necesidad de desplegar/mantener el servicio Piper dedicado — cumple el no-negociable #3.
- El agent worker depende de que el servicio `kokoro-tts` sea alcanzable por red interna desde donde corra el worker — esto es exactamente la tarea abierta 4.4 en `docs/PLAN.md` (networking interno de Coolify), no resuelta aún.
- `piper/` queda en el repo como código histórico, marcado `SUPERSEDED`, sin ser parte del despliegue vigente.
- Cambio de código: commit `d5142db` (`agent/plugins/tts_kokoro_http.py` nuevo, `agent/agent.py`, `agent/requirements.txt` actualizados).
- Riesgo no eliminado del todo: el sample rate nativo real de Kokoro no está confirmado por documentación oficial — mitigado por el hecho verificado de que `AudioStreamDecoder` remuestrea, pero si en producción se detecta audio distorsionado, revisar primero esta asunción antes que otras causas.
