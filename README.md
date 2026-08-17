# Agente de Voz IA — 100% Open Source y Gratuito

Documentación técnica del proceso de construcción de un agente conversacional de voz (STT → LLM → TTS en tiempo real) usando exclusivamente componentes open source, autoalojado en un VPS propio, sin dependencias de APIs de pago. Este repositorio es el material de referencia para una serie en YouTube que documenta la construcción completa, desde cero.

**Estado actual: Etapas 1-5 construidas (código + infraestructura como código), pendientes de probar en un VPS real.** Todo el código de `agent/`, `server/`, `piper/`, `docker/`, `web/` y `scripts/` está escrito y verificado contra el código fuente real de `livekit-agents==1.6.10`, pero no se ha ejecutado de punta a punta contra un LiveKit Server real — este entorno de construcción no tenía acceso a tu VPS. La Etapa 6 (pruebas en la infraestructura real) queda pendiente. Ver [`docs/08-instalacion-despliegue.md`](./docs/08-instalacion-despliegue.md) para desplegarlo.

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
| Detección de turno de conversación | `inference.TurnDetector(version="v1-mini")` | LiveKit Model License, gratis | CPU, local |
| Voz a texto (STT) | faster-whisper | MIT | CPU/GPU, local |
| Modelo de lenguaje (LLM) | Ollama + Qwen2.5-7B-Instruct o Llama-3.1-8B-Instruct | Apache-2.0 / Llama Community License | CPU/GPU, local |
| Texto a voz (TTS) | Piper (fork OHF-Voice/piper1-gpl) | GPL-3.0-or-later | CPU, local |

Detalle completo, alternativas evaluadas y justificación de cada elección en [`docs/`](./docs).

## Estructura del repositorio

```
docs/     — investigación, arquitectura, decisiones (Etapa 1)
agent/    — worker del agente: VAD + STT (faster-whisper) + LLM (Ollama) + TTS (Piper)
server/   — servidor de tokens LiveKit (FastAPI) para la landing page
piper/    — imagen Docker del servidor HTTP de Piper TTS
docker/   — docker-compose.yml, config de LiveKit Server, Caddyfile (TLS)
web/      — landing page mínima de validación (LiveKit Client SDK)
scripts/  — setup del VPS, render de config, descarga del modelo LLM
```

## Índice de documentación

1. [Arquitectura del sistema](./docs/01-arquitectura.md)
2. [Componentes: comparativa y elección técnica](./docs/02-componentes.md)
3. [Frameworks alternativos evaluados (Pipecat, Bolna, TEN, Vocode, FastRTC)](./docs/03-alternativas-frameworks.md)
4. [Requisitos de VPS y checklist de hardware](./docs/04-requisitos-vps.md)
5. [Telefonía / SIP: el único componente que puede no ser 100% gratis](./docs/05-telefonia-sip.md)
6. [Roadmap del proyecto y de la serie de YouTube](./docs/06-roadmap.md)
7. [Cliente de validación: landing page web](./docs/07-cliente-web-landing.md)
8. [Instalación y despliegue en el VPS](./docs/08-instalacion-despliegue.md)

## Advertencia de honestidad técnica

"100% gratis" aplica al software y al cómputo (todo corre en hardware propio con modelos de pesos abiertos). Si en una etapa posterior se agrega telefonía real (PSTN, llamadas desde un número de teléfono), ese tramo específico normalmente requiere un troncal SIP o número, que rara vez es gratuito de forma indefinida. Esto está documentado explícitamente en [`docs/05-telefonia-sip.md`](./docs/05-telefonia-sip.md) para no vender un "gratis" que no se sostiene.

## Licencia

Documentación bajo MIT. Ver [`LICENSE`](./LICENSE).
