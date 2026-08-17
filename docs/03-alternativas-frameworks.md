# Frameworks alternativos evaluados

Ningún framework de agentes de voz de producción es "gratis" por sí mismo en el sentido de traer STT/LLM/TTS incluidos — todos son capas de orquestación que se conectan a proveedores. La gratuidad real depende de qué proveedores se conectan (ver [`02-componentes.md`](./02-componentes.md)). Esta tabla compara la capa de orquestación, no el pipeline completo.

| Framework | Licencia | Modelo de transporte | Telefonía nativa | Curva de aprendizaje | Por qué no se eligió |
|---|---|---|---|---|---|
| **LiveKit Agents** ✅ elegido | Apache-2.0 | WebRTC + media server propio (self-hosted) | Sí, SIP nativo | Media (concepto de "rooms") | — |
| Pipecat | BSD-2-Clause | No trae media server propio; requiere Daily, WebSockets o Twilio | Vía Twilio | Baja-media | Más control y menos vendor lock-in, pero obliga a resolver transporte WebRTC por separado — más piezas móviles para un proyecto reproducible en video |
| TEN Framework | Apache-2.0 (híbrida) | Depende de la red de Agora | Vía Agora | Media-alta | Licencia híbrida con restricciones comerciales; depende de Agora App ID y cuota gratuita limitada — no es autoalojable al 100% |
| Bolna | MIT | Telefonía-first, requiere Twilio/Plivo/Exotel | Sí (vía carriers de pago) | Baja | Diseñado para telefonía desde el día uno, lo cual implica costos de carrier casi de inmediato; comunidad pequeña |
| Vocode | MIT | Twilio/Vonage | Vía Twilio/Vonage | Baja | Mantenimiento detenido (último commit nov. 2024); riesgo de obsolescencia |
| FastRTC | MIT | WebRTC/WebSocket ligero | No (requiere puente externo tipo Jambonz) | Alta (hay que construir orquestación propia) | Muy minimalista: VAD, interrupciones y turn-taking quedan a cargo del desarrollador — más trabajo de ingeniería que valor para este proyecto |

## Conclusión

LiveKit Agents es la única opción que combina: media server self-hosted incluido (sin depender de Daily, Agora o Twilio para el transporte de audio), SIP nativo por si se agrega telefonía después, y un turn-detector propio que es gratuito incluso fuera de su nube. El costo es una curva de aprendizaje algo mayor (el modelo de "rooms y participantes" de WebRTC) y menor flexibilidad para intercambiar proveedores — irrelevante aquí porque los proveedores ya están fijados a componentes locales y gratuitos.
