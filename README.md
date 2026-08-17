# Agente de Voz IA — 100% Open Source y Gratuito

Documentación técnica del proceso de construcción de un agente conversacional de voz (STT → LLM → TTS en tiempo real) usando exclusivamente componentes open source, autoalojado en un VPS propio, sin dependencias de APIs de pago. Este repositorio es el material de referencia para una serie en YouTube que documenta la construcción completa, desde cero.

**Estado actual: Etapa 1 — Investigación y diseño de arquitectura.** No hay código todavía. Esta etapa define qué se va a construir y con qué piezas, antes de tocar una sola línea.

## Objetivo

Un agente de voz conversacional en tiempo real (interrumpible, baja latencia, streaming) que corra íntegramente en infraestructura propia:

- Sin API keys de pago (OpenAI, ElevenLabs, Deepgram, etc.)
- Sin límites de uso ni facturación por minuto/token
- Con privacidad total: el audio y las transcripciones nunca salen del VPS
- Reproducible por cualquiera que siga la documentación

## Stack elegido (resumen)

| Capa | Componente | Licencia | Corre en |
|---|---|---|---|
| Orquestador / transporte de audio | [LiveKit Agents](https://github.com/livekit/agents) + LiveKit Server | Apache-2.0 | VPS (Docker) |
| Detección de voz (VAD) | Silero VAD | MIT | CPU, local |
| Detección de turno de conversación | LiveKit Turn Detector (v1-mini) | LiveKit Model License, gratis | CPU, local |
| Voz a texto (STT) | faster-whisper | MIT | CPU/GPU, local |
| Modelo de lenguaje (LLM) | Ollama + Qwen2.5-7B-Instruct o Llama-3.1-8B-Instruct | Apache-2.0 / Llama Community License | CPU/GPU, local |
| Texto a voz (TTS) | Piper | MIT | CPU, local |

Detalle completo, alternativas evaluadas y justificación de cada elección en [`docs/`](./docs).

## Índice de documentación

1. [Arquitectura del sistema](./docs/01-arquitectura.md)
2. [Componentes: comparativa y elección técnica](./docs/02-componentes.md)
3. [Frameworks alternativos evaluados (Pipecat, Bolna, TEN, Vocode, FastRTC)](./docs/03-alternativas-frameworks.md)
4. [Requisitos de VPS y checklist de hardware](./docs/04-requisitos-vps.md)
5. [Telefonía / SIP: el único componente que puede no ser 100% gratis](./docs/05-telefonia-sip.md)
6. [Roadmap del proyecto y de la serie de YouTube](./docs/06-roadmap.md)

## Advertencia de honestidad técnica

"100% gratis" aplica al software y al cómputo (todo corre en hardware propio con modelos de pesos abiertos). Si en una etapa posterior se agrega telefonía real (PSTN, llamadas desde un número de teléfono), ese tramo específico normalmente requiere un troncal SIP o número, que rara vez es gratuito de forma indefinida. Esto está documentado explícitamente en [`docs/05-telefonia-sip.md`](./docs/05-telefonia-sip.md) para no vender un "gratis" que no se sostiene.

## Licencia

Documentación bajo MIT. Ver [`LICENSE`](./LICENSE).
