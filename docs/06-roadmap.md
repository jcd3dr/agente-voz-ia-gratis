# Roadmap del proyecto y de la serie de YouTube

## Etapa 1 — Investigación y arquitectura (este repositorio, completada)

- Selección de framework de orquestación (LiveKit Agents)
- Selección de STT, LLM, TTS, VAD y turn detection 100% gratuitos y autoalojables
- Definición de requisitos de VPS
- Documentación honesta de la única excepción de gratuidad (telefonía PSTN)

## Etapa 2 — Preparación del VPS

- Verificación de specs del VPS contra [`04-requisitos-vps.md`](./04-requisitos-vps.md)
- Instalación de Docker, Docker Compose
- Configuración de dominio + TLS (Caddy o Nginx+Certbot)
- Apertura de puertos necesarios para LiveKit

## Etapa 3 — Despliegue de LiveKit Server

- `docker-compose` con LiveKit Server + Redis
- Verificación de conectividad WebRTC (test de sala básica)

## Etapa 4 — Instalación de componentes de IA

- Ollama + descarga de Qwen2.5-7B-Instruct
- faster-whisper (modelo medium, cuantizado int8)
- Piper + voz en español

## Etapa 5 — Construcción del agente (worker)

- Agent en Python con LiveKit Agents SDK
- Pipeline VAD → turn detector → STT → LLM → TTS conectado end-to-end
- Manejo de interrupciones (barge-in)

## Etapa 6 — Pruebas y ajuste de latencia

- Medición de latencia real por etapa
- Tuning de parámetros (tamaño de modelo, streaming, buffers)

## Etapa 7 — Demo pública y cierre de la serie

- Cliente web mínimo para probar el agente desde navegador
- Grabación de la demo final para el video de cierre

---

Cada etapa a partir de la 2 corresponde a un video/capítulo separado de la serie. Este repositorio se irá actualizando con el código y la documentación de cada etapa conforme se construya — no antes.
