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

import asyncio
import json
import logging
import os

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    APIConnectOptions,
    JobContext,
    JobProcess,
    TurnHandlingOptions,
    cli,
    inference,
)
from livekit.agents.voice.agent_session import SessionConnectOptions
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
# OJO: NO usar os.cpu_count() a secas aca. num_idle_processes (mas abajo)
# hace que el pool arranque VARIOS procesos de reserva EN PARALELO al inicio,
# cada uno cargando su propio modelo Whisper - si cada uno pide TODOS los
# cores, terminan compitiendo entre si por los mismos threads (ej. 4 procesos
# x 6 threads = 24 threads peleando por 6 cores reales), y la carga se vuelve
# tan lenta que supera initialize_process_timeout (10s default) y el proceso
# se mata solo. Confirmado en logs reales: "TimeoutError" + "process exited
# with non-zero exit code -10" en los 4 procesos de reserva simultaneos.
# Con NUM_IDLE_PROCESSES=1 (ver mas abajo) un valor mas alto si seria seguro,
# pero se deja moderado por las dudas de que se suba ese numero despues.
WHISPER_CPU_THREADS = int(os.getenv("WHISPER_CPU_THREADS", "4"))
# beam_size=5 (default de faster-whisper) es mas preciso pero mas lento en
# CPU que beam_size=1 (greedy). Configurable para poder comparar sin tocar
# codigo - ver docs/PLAN.md para el resultado de la comparacion.
WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
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


# num_idle_processes default es 4 en modo produccion ("start", que es como
# corre este contenedor). Para pruebas de una sola persona a la vez eso es
# desperdicio de RAM (4 copias del modelo Whisper cargadas) y, combinado con
# WHISPER_CPU_THREADS alto, fue la causa real de que el prewarm timeoutee
# (ver comentario de WHISPER_CPU_THREADS arriba). 1 alcanza para probar solo.
server = AgentServer(num_idle_processes=1)


def prewarm(proc: JobProcess) -> None:
    """Corre UNA vez por proceso worker, antes de que llegue ningun job -
    no una vez por sesion/participante. Sin esto, el VAD (Silero) y el modelo
    de faster-whisper se cargarian desde cero cada vez que entrypoint()
    arranca para una sesion nueva, sumando esa carga al "tiempo hasta la
    primera respuesta" de cada usuario que se conecta. Guardado en
    proc.userdata para que entrypoint() lo reutilice via ctx.proc.userdata.
    """
    proc.userdata["vad"] = silero.VAD.load(min_silence_duration=0.7)
    proc.userdata["stt"] = FasterWhisperSTT(
        model_size=WHISPER_MODEL_SIZE,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
        language=AGENT_LANGUAGE,
        cpu_threads=WHISPER_CPU_THREADS,
        beam_size=WHISPER_BEAM_SIZE,
        download_root=WHISPER_DOWNLOAD_ROOT,
    )


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=ctx.proc.userdata["stt"],
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
            # Al ser un turn-detector "streaming", livekit-agents usa por
            # defecto min_delay=0.3s/max_delay=2.5s (mas agresivo que el
            # default "fixed" de 0.5s/3.0s) - corta el turno apenas 0.3s de
            # silencio, lo cual obliga a hablar rapido para no ser cortado a
            # mitad de frase. min_delay subido un poco para tolerar pausas
            # naturales cortas. max_delay se dejo CASI en el default (2.5s):
            # subirlo a 4.0s (probado antes) resulto contraproducente - cuando
            # el modelo de turn-detection duda (pasa seguido en español),
            # espera hasta max_delay antes de decidir, asi que un max_delay
            # alto se convierte en el peor caso *tipico*, no una excepcion.
            endpointing={"min_delay": 0.6, "max_delay": 2.8},
        ),
        # Default de livekit-agents es timeout=10s para el LLM. Ollama en CPU
        # tarda ~8-10s solo en cargar el modelo a RAM la primera vez que se le
        # pide algo (o si quedo descargado tras OLLAMA_KEEP_ALIVE) - eso solo ya
        # se come el timeout default y tira APITimeoutError. Subido a 30s.
        conn_options=SessionConnectOptions(
            llm_conn_options=APIConnectOptions(timeout=30.0),
        ),
    )

    # Instrumentacion para el visualizador de pipeline del web/index.html: manda
    # estado (listening/thinking/speaking), transcript y metricas por etapa
    # (STT/LLM/TTS/turn-detection) como mensajes de datos de LiveKit, asi el
    # navegador puede mostrar en vivo donde se esta yendo el tiempo.
    #
    # publish_data() ES una coroutine (a pesar de que su firma declara -> None;
    # esa anotacion de tipo esta mal en el stub) - verificado en runtime por un
    # RuntimeWarning real de "coroutine was never awaited". Como los handlers de
    # session.on() son funciones sincronas (no se pueden declarar async), hay
    # que agendarla con asyncio.create_task(). Ademas, el primer evento de
    # estado puede dispararse antes de que ctx.room termine de conectar
    # (ctx.room.local_participant tira si todavia no hay conexion) - se
    # ignora silenciosamente porque esto es solo telemetria para la UI, nunca
    # debe poder romper el pipeline de voz real.
    def _publish(payload: dict) -> None:
        try:
            asyncio.create_task(
                ctx.room.local_participant.publish_data(
                    json.dumps(payload).encode("utf-8"), topic="pipeline"
                )
            )
        except Exception:
            logger.debug("no se pudo publicar evento de pipeline", exc_info=True)

    @session.on("agent_state_changed")
    def _on_state_changed(ev) -> None:
        _publish({"kind": "state", "state": ev.new_state})

    @session.on("user_input_transcribed")
    def _on_transcript(ev) -> None:
        if ev.is_final:
            logger.info("[PIPELINE] transcript final: %r", ev.transcript)
            _publish({"kind": "transcript", "text": ev.transcript})

    # STAGE_LABELS mapea la clase de metrica de livekit-agents a una etiqueta
    # fija en el log, para poder grepear "[PIPELINE] STT" / "LLM" / "TTS" /
    # "Turno" y ver cada etapa por separado en vez de un solo blob de JSON.
    _STAGE_LABELS = {
        "STTMetrics": "STT",
        "LLMMetrics": "LLM",
        "TTSMetrics": "TTS",
        "EOUMetrics": "Turno (fin de tu habla -> se dispara el LLM)",
    }

    @session.on("metrics_collected")
    def _on_metrics(ev) -> None:
        m = ev.metrics
        stage = type(m).__name__
        # VADMetrics (y cualquier otra metrica que livekit-agents agregue a
        # futuro fuera de las 4 que nos interesan) se dispara muy seguido y
        # sin datos utiles para nosotros - sin este filtro inundaba el log y
        # el panel del navegador, tapando las etiquetas de STT/LLM/TTS/Turno
        # casi al instante.
        if stage not in _STAGE_LABELS:
            return
        label = _STAGE_LABELS[stage]
        data = {"kind": "metrics", "stage": stage}
        parts = []
        for field, human in (
            ("duration", "duracion_total_ms"),
            ("ttft", "tiempo_al_primer_token_ms"),
            ("ttfb", "tiempo_al_primer_audio_ms"),
            ("end_of_utterance_delay", "delay_deteccion_fin_turno_ms"),
        ):
            value = getattr(m, field, None)
            if value is not None:
                ms = round(value * 1000)
                data[field] = ms
                parts.append(f"{human}={ms}ms")
        logger.info("[PIPELINE] %s: %s", label, ", ".join(parts))
        _publish(data)

    await session.start(agent=Asistente(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
