"""Worker del agente de voz: conecta VAD + turn detection + STT + LLM + TTS,
todo 100% local/gratis, a una sala de LiveKit self-hosted.

Patrón de entrypoint (AgentServer + @server.rtc_session) y todas las clases
importadas (AgentSession, TurnHandlingOptions, inference.TurnDetector, silero.VAD,
openai.LLM.with_ollama) verificados contra el código fuente real de
livekit-agents==1.6.10 (github.com/livekit/agents, tag v1.6.10) — no inventados.

Ejecutar (dentro del contenedor, ver agent/Dockerfile):
    python3 agent.py start
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
)
from livekit.plugins import openai, silero

from plugins.stt_faster_whisper import FasterWhisperSTT
from plugins.tts_kokoro_http import KokoroTTS

load_dotenv()

logger = logging.getLogger("agente-voz-gratis")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama-api:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
KOKORO_BASE_URL = os.getenv("KOKORO_BASE_URL", "http://kokoro-tts:8880")
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "ef_dora")
# "small" (~500MB) por defecto en vez de "medium" (~1.5GB): descarga más rápida y
# liviana en un VPS con recursos compartidos con otros servicios (ollama, kokoro,
# n8n, etc). Se puede subir a "medium"/"large-v3" vía env var si el VPS lo soporta.
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
# Directorio persistente (montado como volumen en el despliegue real) para que el
# modelo de faster-whisper se descargue una sola vez y no en cada reinicio del
# contenedor. Ver docs/08-instalacion-despliegue.md.
WHISPER_DOWNLOAD_ROOT = os.getenv("WHISPER_DOWNLOAD_ROOT") or None
AGENT_LANGUAGE = os.getenv("AGENT_LANGUAGE", "es")

INSTRUCTIONS = (
    "Eres un asistente de voz conversacional que habla español. "
    "Responde siempre de forma breve, natural y directa, como en una llamada telefónica real. "
    "No uses emojis, asteriscos, markdown, ni ningún caracter especial de formato: "
    "todo lo que escribas se convierte directamente en audio."
)


class Asistente(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Saluda brevemente al usuario y pregúntale en qué puedes ayudarlo."
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=FasterWhisperSTT(
            model_size=WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
            language=AGENT_LANGUAGE,
            download_root=WHISPER_DOWNLOAD_ROOT,
        ),
        # Ollama expone una API compatible con OpenAI; el plugin oficial
        # openai.LLM.with_ollama() solo cambia base_url y api_key="ollama".
        llm=openai.LLM.with_ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
        ),
        tts=KokoroTTS(base_url=KOKORO_BASE_URL, voice=KOKORO_VOICE),
        turn_handling=TurnHandlingOptions(
            # v1-mini corre localmente en CPU, sin llamadas a la nube de LiveKit.
            turn_detection=inference.TurnDetector(version="v1-mini"),
        ),
    )

    await session.start(agent=Asistente(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
