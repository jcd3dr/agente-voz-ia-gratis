# 0003 — TTS: Piper

## Status

Superseded by ADR-0004

## Context

El pipeline necesita una capa de TTS (texto a voz) 100% gratuita, autoalojable en el VPS, con voces en español de calidad razonable para una demo/serie de YouTube.

## Decision

Se eligió **Piper TTS**, empaquetado como imagen Docker propia (`piper/`), desplegado como servicio dedicado del proyecto.

Durante la evaluación de licencia se detectó y corrigió un error inicial: se había asumido licencia MIT; la licencia real de Piper es **GPL-3.0-or-later**. Se documentó como precedente en `AGENTS.md` (sección "Convenciones") la regla de que copyleft (GPL) es aceptable si el componente se consume como servicio HTTP externo, no si se enlaza/modifica su código dentro de este repo — condición que Piper cumplía (se consume vía HTTP, no se importa como librería).

## Consequences

- Requería desplegar y mantener un servicio Piper dedicado, propio de este proyecto, en el VPS.
- Esta decisión fue **superseded** por ADR-0004: se descubrió que el VPS del usuario ya corre un servicio Kokoro-FastAPI (`kokoro-tts`) para otro proyecto, y el no-negociable #3 ("no duplicar infraestructura ya viva") hace preferible reutilizarlo en vez de mantener un Piper redundante.
- El directorio `piper/` permanece en el repo como referencia histórica (imagen Docker funcional), marcado explícitamente como no usado en el despliegue actual — ver `AGENTS.md`, sección "Estructura del repositorio".
