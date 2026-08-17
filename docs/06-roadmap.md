# Roadmap del proyecto y de la serie de YouTube

## Etapa 1 — Investigación y arquitectura (este repositorio, completada)

- Selección de framework de orquestación (LiveKit Agents)
- Selección de STT, LLM, TTS, VAD y turn detection 100% gratuitos y autoalojables
- Definición de requisitos de VPS
- Documentación honesta de la única excepción de gratuidad (telefonía PSTN)
- Definición del cliente de validación: landing page web mínima (ver [`07-cliente-web-landing.md`](./07-cliente-web-landing.md))

## Etapa 2 — Preparación del VPS

- Verificación de specs del VPS contra [`04-requisitos-vps.md`](./04-requisitos-vps.md)
- Instalación de Docker, Docker Compose
- Configuración de dominio + TLS (Caddy o Nginx+Certbot) — requisito obligatorio para que la landing page pueda pedir permiso de micrófono
- Apertura de puertos necesarios para LiveKit

## Etapa 3 — Despliegue de LiveKit Server + landing page mínima

- `docker-compose` con LiveKit Server + Redis
- Servidor de tokens (endpoint que firma JWT de acceso a sala)
- Landing page mínima (HTML + LiveKit Client SDK) para pedir micrófono y conectarse a una sala
- Verificación de conectividad WebRTC (test de sala básica, sin agente todavía)

## Etapa 4 — Instalación de componentes de IA

- Ollama + descarga de Qwen2.5-7B-Instruct
- faster-whisper (modelo medium, cuantizado int8)
- Piper + voz en español

## Etapa 5 — Construcción del agente (worker)

- Agent en Python con LiveKit Agents SDK
- Pipeline VAD → turn detector → STT → LLM → TTS conectado end-to-end
- Manejo de interrupciones (barge-in)
- **Primera prueba real de punta a punta**: hablar con el agente desde la landing page construida en la Etapa 3

## Etapa 6 — Pruebas y ajuste de latencia

- Medición de latencia real por etapa
- Tuning de parámetros (tamaño de modelo, streaming, buffers)

## Etapa 7 — Demo pública y cierre de la serie

- Pulido de la landing page (UI, indicadores de estado: escuchando/pensando/hablando)
- Grabación de la demo final para el video de cierre

---

Cada etapa a partir de la 2 corresponde a un video/capítulo separado de la serie. Este repositorio se irá actualizando con el código y la documentación de cada etapa conforme se construya — no antes.
