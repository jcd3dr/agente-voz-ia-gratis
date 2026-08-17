# Arquitectura del sistema

## Flujo de datos (pipeline conversacional)

```
Usuario (navegador / app / SIP)
        │  audio WebRTC (Opus)
        ▼
┌─────────────────────────────────────────────┐
│  LiveKit Server (media server, self-hosted)  │  ← enruta el audio en tiempo real
└─────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│  LiveKit Agent (worker Python/Node)          │
│                                               │
│  1. Silero VAD        → detecta si hay voz   │
│  2. Turn Detector      → decide cuándo el    │
│     (v1-mini)            usuario terminó de  │
│                           hablar (evita       │
│                           interrupciones      │
│                           prematuras)         │
│  3. faster-whisper STT → audio → texto        │
│     (streaming)                              │
│  4. Ollama LLM         → texto → respuesta    │
│     (streaming tokens)   (streaming)          │
│  5. Piper TTS          → respuesta → audio    │
│     (streaming)                              │
└─────────────────────────────────────────────┘
        │  audio WebRTC (Opus)
        ▼
Usuario (escucha la respuesta)
```

Todo el pipeline corre **streaming**: no se espera a que el usuario termine de hablar por completo para empezar a transcribir, ni a que el LLM termine de generar para empezar a sintetizar voz. Esto es lo que hace la diferencia entre un agente que se siente "conversacional" y uno que se siente como un contestador automático.

## Por qué LiveKit como orquestador

LiveKit Agents no es solo un framework de lógica: incluye el **media server** (basado en WebRTC) que resuelve la parte más difícil de un agente de voz — enrutar audio en tiempo real, manejar reconexiones, jitter buffer, eco, múltiples participantes. Al ser self-hosted (Apache-2.0), se elimina la dependencia de LiveKit Cloud.

La alternativa (Pipecat) da más libertad para intercambiar proveedores con una línea de código, pero deja la infraestructura de transporte (WebRTC/websockets) a cargo del operador. Para un proyecto pensado para reproducirse en un video paso a paso, minimizar piezas móviles de infraestructura pesa más que la flexibilidad de swap de proveedores — sobre todo porque aquí **todos los componentes ya son fijos y locales** (no hay proveedores que intercambiar).

Detalle de la comparación completa en [`03-alternativas-frameworks.md`](./03-alternativas-frameworks.md).

## Despliegue físico en el VPS

```
VPS (Ubuntu 22.04+, Docker)
│
├── contenedor: livekit-server        (puertos 7880/tcp, 7881/tcp, 50000-60000/udp)
├── contenedor: redis                 (requerido por livekit-server para estado)
├── proceso:    livekit-agent-worker  (Python, se conecta al server vía WS)
├── proceso:    ollama serve          (puerto 11434, sirve el LLM)
└── modelos locales en disco:
    ├── faster-whisper (medium o large-v3-turbo, ~1.5-3 GB)
    ├── Piper (voz es_ES o es_MX, ~60 MB)
    └── Ollama (Qwen2.5-7B-Instruct Q4_K_M, ~4.5 GB)
```

Nginx o Caddy como reverse proxy con TLS delante de LiveKit server (necesario para WebRTC en producción — los navegadores exigen HTTPS/WSS para capturar micrófono fuera de localhost).

## Puntos de latencia crítica

| Etapa | Latencia esperada (CPU, sin GPU) | Latencia esperada (con GPU) |
|---|---|---|
| VAD + turn detection | ~20-50 ms | ~20-50 ms |
| STT (faster-whisper, streaming) | ~300-600 ms | ~100-200 ms |
| LLM time-to-first-token (7B) | ~800-1500 ms | ~150-300 ms |
| TTS time-to-first-audio (Piper) | ~200-400 ms | ~150-300 ms |
| **Total percibido hasta primera respuesta audible** | **~1.5-2.5 s** | **~0.5-1 s** |

Ver requisitos de hardware y cómo mitigar la latencia en CPU en [`04-requisitos-vps.md`](./04-requisitos-vps.md).
