# Requisitos de VPS

## Especificación mínima recomendada

| Recurso | Mínimo viable | Recomendado | Óptimo (con GPU) |
|---|---|---|---|
| vCPU | 4 | 8 | 8+ |
| RAM | 8 GB | 16 GB | 16-32 GB |
| Disco | 30 GB SSD/NVMe | 50 GB NVMe | 50 GB NVMe |
| GPU | No requerida | No requerida | RTX 4060 (8GB) o superior |
| Ancho de banda | 100 Mbps | 1 Gbps | 1 Gbps |
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Requisito de CPU | AVX2 (obligatorio para Ollama/faster-whisper cuantizados) | AVX2 | AVX2 |

Con 8GB RAM el sistema es *funcionalmente* posible pero ajustado: Ollama por sí solo pide 8GB como mínimo absoluto documentado por el proyecto, y hay que compartir esa RAM con LiveKit server, el worker del agente y faster-whisper. **16GB es el punto donde el sistema deja de estar al límite.**

## Verificar si el VPS actual cumple

```bash
# CPU y soporte AVX2 (obligatorio)
lscpu | grep -i avx2

# Núcleos disponibles
nproc

# RAM total
free -h

# Espacio en disco
df -h

# Si hay GPU NVIDIA disponible
nvidia-smi 2>/dev/null || echo "Sin GPU NVIDIA — se usará inferencia por CPU"
```

Si `lscpu | grep avx2` no devuelve nada, Ollama y faster-whisper en modo cuantizado no van a arrancar correctamente — es un requisito de hardware no negociable, no de software.

## Rendimiento esperado por configuración

| Configuración | Modelo LLM | Tokens/seg (aprox.) | Latencia total percibida |
|---|---|---|---|
| 4 vCPU / 8GB RAM (mínimo) | Qwen2.5-3B o Llama3.2-3B | 8-12 tok/s | ~2-3 s |
| 8 vCPU / 16GB RAM (recomendado) | Qwen2.5-7B / Llama3.1-8B | 5-8 tok/s | ~1.5-2.5 s |
| 8 vCPU / 16GB RAM + GPU 8GB | Qwen2.5-7B/14B | 30-60 tok/s | ~0.5-1 s |

La CPU-only es viable para una demo conversacional fluida, pero no va a competir en naturalidad con agentes comerciales (que corren en GPU dedicada). Para el propósito de este proyecto — demostrar que un agente de voz gratuito y funcional es posible — es más que suficiente.

## Plan B si el VPS no alcanza los mínimos

Si el VPS disponible es más modesto (2-4 vCPU, <8GB RAM), hay dos salidas sin romper el principio de "gratis", aunque sí rompen parcialmente "100% self-hosted":

1. **Modelos más pequeños localmente**: Qwen2.5-3B-Instruct o Llama-3.2-3B-Instruct (caben en 4GB RAM), con faster-whisper `small` en vez de `medium`. Pierde algo de calidad de respuesta y precisión de transcripción, pero sigue siendo 100% local.
2. **LLM en la nube gratis, resto local**: mantener STT (faster-whisper) y TTS (Piper) en el VPS, y delegar solo la inferencia del LLM a un proveedor con capa gratuita generosa para modelos open-weight (por ejemplo Groq, que sirve Llama/Qwen con latencia muy baja sin costo dentro de límites de uso razonables). Esto deja de ser "self-hosted al 100%" pero sigue siendo "$0 de costo". Se documenta como fallback, no como recomendación primaria — la premisa del proyecto es demostrar el stack autoalojado.

## Networking necesario

LiveKit Server necesita estos puertos abiertos en el firewall del VPS:

```
7880/tcp   — API HTTP / WebSocket de LiveKit
7881/tcp   — RTC over TCP (fallback)
50000-60000/udp — rango RTP para medios WebRTC (ajustable en config)
```

Además, **dos subdominios con TLS** (Let's Encrypt vía Caddy, ya automatizado en `docker/Caddyfile`) son necesarios: uno dedicado por completo a LiveKit Server (`livekit.tu-dominio.com`) y otro para la landing page + servidor de tokens (`agente.tu-dominio.com`). Se usan dos subdominios y no rutas bajo un solo dominio porque LiveKit necesita todo el árbol de rutas de su dominio para su propia señalización WebSocket/API — mezclarlo con otras rutas rompe la conexión. Detalle completo en [`08-instalacion-despliegue.md`](./08-instalacion-despliegue.md). HTTPS es obligatorio en ambos: sin TLS, los navegadores bloquean la captura de micrófono fuera de `localhost`.
