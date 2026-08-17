# Componentes: comparativa y elección técnica

Para cada capa del pipeline se evaluaron las opciones open source más relevantes en 2026. Se eligió la que maximiza: (a) gratuidad real sin límites de uso, (b) capacidad de correr en CPU (el VPS no tiene GPU garantizada), (c) soporte de español, (d) mantenimiento activo.

## 1. Voz a texto (STT)

| Modelo | Licencia | Precisión (WER) | Español | Hardware mínimo | Elegido |
|---|---|---|---|---|---|
| **faster-whisper** | MIT | ~2.7% (large-v3) | Excelente | CPU (int8) / GPU 4GB+ | ✅ |
| Whisper (original, OpenAI) | MIT | ~2.7% | Excelente | GPU 10GB+ | — más lento, mismo modelo base |
| Vosk | Apache-2.0 | ~8-10% | Bueno | CPU 50MB | — precisión insuficiente para conversación natural |
| NVIDIA Canary-Qwen 2.5B | CC-BY | ~5.6% | Medio | GPU 8GB+ | — español no es punto fuerte |
| Moonshine Base | MIT | ~7.5% | No soportado | CPU 2GB | — descartado, sin español |

**Elección: faster-whisper**, modelo `medium` o `large-v3-turbo` cuantizado int8. Es una reimplementación de Whisper sobre CTranslate2 que da la misma precisión con ~4x más velocidad en CPU, viable para streaming en tiempo real sin GPU.

## 2. Modelo de lenguaje (LLM)

| Modelo | Licencia | Tamaño viable en VPS CPU | Español | Elegido |
|---|---|---|---|---|
| **Qwen2.5-7B-Instruct** | Apache-2.0 | Q4_K_M, ~4.5GB RAM | Muy bueno | ✅ (opción primaria) |
| **Llama-3.1-8B-Instruct** | Llama 3.1 Community License | Q4_K_M, ~5GB RAM | Muy bueno | ✅ (alternativa) |
| Mistral-7B-Instruct | Apache-2.0 | Q4_K_M, ~4.5GB RAM | Bueno | — viable, menor razonamiento que Qwen2.5 |
| DeepSeek/Qwen 32B+ | Variadas | 18-22GB RAM | Excelente | — descartado, no cabe en VPS típico de CPU |

**Elección: Qwen2.5-7B-Instruct vía Ollama.** Corre en un VPS de 16GB RAM sin GPU a 5-8 tok/s (usable para conversación con streaming). Si el VPS tiene GPU, se puede escalar a Qwen2.5-14B para mejor calidad de respuesta.

Servidor de inferencia: **Ollama** (simplifica gestión de modelos y expone API HTTP local compatible con OpenAI). Alternativa más eficiente pero más compleja de operar: vLLM o llama.cpp puro.

## 3. Texto a voz (TTS)

| Modelo | Licencia | Español | Latencia | Clonación de voz | Hardware | Elegido |
|---|---|---|---|---|---|---|
| **Piper** | MIT | Nativo (varias voces es_ES/es_MX/es_AR) | <500 ms | No | Solo CPU | ✅ |
| XTTS-v2 (Coqui) | Coqui Public Model License | Nativo | 3-5 s | Sí (6 seg de audio) | GPU 4GB+ | — más lento, licencia no-MIT |
| Kokoro | Apache-2.0 | Limitado | Baja | No | CPU/GPU ligero | — menos voces en español que Piper |
| Fish Speech | Open source | Sí | 1-2 s | Sí | GPU 4GB+ | — requiere GPU |
| StyleTTS 2 | Open source | Limitado (14 idiomas) | 2-3 s | Sí | GPU 2GB+ | — español no confirmado como fuerte |

**Elección: Piper.** Es la única opción de calidad "muy buena" que corre exclusivamente en CPU con latencia sub-segundo, condición obligatoria dado que el VPS no garantiza GPU. Si en una fase posterior se añade GPU al VPS, XTTS-v2 es el upgrade natural por clonación de voz y mayor naturalidad prosódica.

## 4. Detección de actividad de voz (VAD)

**Elección: Silero VAD** (MIT). Viene integrado como plugin nativo de LiveKit Agents, corre en CPU en <1ms por frame, es el estándar de facto en el ecosistema.

## 5. Detección de turno de conversación (turn detection)

**Elección: LiveKit Turn Detector, modelo `v1-mini`.** Es gratuito para cualquier uso (no solo LiveKit Cloud), corre localmente en CPU, requiere <500MB RAM, y soporta español de forma nativa (14 idiomas). Resuelve el problema de que el VAD por sí solo no distingue una pausa para pensar de un turno terminado — reduce interrupciones prematuras del agente.

## 6. Orquestador / transporte

**Elección: LiveKit Agents + LiveKit Server** (Apache-2.0). Justificación completa en [`01-arquitectura.md`](./01-arquitectura.md) y comparación con alternativas en [`03-alternativas-frameworks.md`](./03-alternativas-frameworks.md).
