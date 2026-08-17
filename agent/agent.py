"""Worker del agente de voz: conecta VAD + turn detection + STT + LLM + TTS,
todo 100% local/gratis, a una sala de LiveKit self-hosted.

Patron de entrypoint (AgentServer + @server.rtc_session) y todas las clases
importadas (AgentSession, TurnHandlingOptions, inference.TurnDetector, silero.VAD,
openai.LLM.with_ollama) verificados contra el codigo fuente real de
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
from plugins.tts_piper_http import PiperTTS

load_dotenv()

logger = logging.getLogger("agente-voz-gratis")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
PIPER_BASE_URL = os.getenv("PIPER_BASE_URL", "http://piper:5000")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
AGENT_LANGUAGE = os.getenv("AGENT_LANGUAGE", "es")

INSTRUCTIONS = (
    "Eres un asistente de voz conversacional que habla espanol. "
    "Responde siempre de forma breve, natural y directa, como en una llamada telefonica real. "
    "No uses emojis, asteriscos, markdown, ni ningun caracter especial de formato: "
    "todo lo que escribas se convierte directamente en audio."
)


class Asistente(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Saluda brevemente al usuario y preguntale en que puedes ayudarlo."
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
        ),
        # Ollama expone una API compatible con OpenAI; el plugin oficial
        # openai.LLM.with_ollama() solo cambia base_url y api_key="ollama".
        llm=openai.LLM.with_ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
        ),
        tts=PiperTTS(base_url=PIPER_BASE_URL),
        turn_handling=TurnHandlingOptions(
            # v1-mini corre localmente en CPU, sin llamadas a la nube de LiveKit.
            turn_detection=inference.TurnDetector(version="v1-mini"),
        ),
    )

    await session.start(agent=Asistente(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
