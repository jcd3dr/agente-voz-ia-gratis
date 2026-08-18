"""STT local con faster-whisper (CTranslate2), sin dependencia de ninguna API de pago.

Implementa la interfaz batch (`_recognize_impl`) de `livekit.agents.stt.STT`.
Al declarar `STTCapabilities(streaming=False, ...)`, el framework de LiveKit Agents
envuelve automaticamente esta clase en un `stt.StreamAdapter` que usa el VAD (Silero)
de la sesion para trocear el audio por turno de habla y llamar a `recognize()` una
vez por turno — no hace falta implementar streaming a mano.

Referencia de la interfaz verificada contra el codigo fuente real de
livekit-agents==1.6.10 (paquete `livekit-plugins-fal`, clase WizperSTT, como
plantilla del patron batch) y `livekit.agents.stt.stt.STT`.
"""

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass

from livekit import rtc
from livekit.agents import APIConnectionError, APIConnectOptions, LanguageCode, stt
from livekit.agents.stt import SpeechEventType, STTCapabilities
from livekit.agents.types import NOT_GIVEN, NotGivenOr
from livekit.agents.utils import AudioBuffer, is_given

from faster_whisper import WhisperModel


@dataclass
class _STTOptions:
    language: str


class FasterWhisperSTT(stt.STT):
    """Reconocimiento de voz 100% local usando faster-whisper.

    El modelo se carga una sola vez, de forma bloqueante, al construir el worker
    (proceso de inicio del contenedor `agent`). Cada llamada a `recognize()` corre
    la inferencia en un hilo aparte (`run_in_executor`) para no bloquear el event
    loop de asyncio mientras el CPU transcribe.
    """

    def __init__(
        self,
        *,
        model_size: str = "medium",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "es",
        cpu_threads: int = 4,
        beam_size: int = 5,
        download_root: str | None = None,
    ) -> None:
        super().__init__(capabilities=STTCapabilities(streaming=False, interim_results=False))
        self._opts = _STTOptions(language=language)
        self._beam_size = beam_size
        self._model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            download_root=download_root,
        )

    @property
    def model(self) -> str:
        return "faster-whisper"

    @property
    def provider(self) -> str:
        return "local"

    def update_options(self, *, language: NotGivenOr[str] = NOT_GIVEN) -> None:
        if is_given(language):
            self._opts.language = language

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        lang = language if is_given(language) else self._opts.language
        wav_bytes = rtc.combine_audio_frames(buffer).to_wav_bytes()
        loop = asyncio.get_running_loop()

        def _transcribe() -> str:
            segments, _info = self._model.transcribe(
                io.BytesIO(wav_bytes),
                language=lang or None,
                beam_size=self._beam_size,
                # el VAD de la sesion (Silero) ya delimito el turno de habla;
                # no hace falta que faster-whisper vuelva a filtrar silencio.
                vad_filter=False,
            )
            return "".join(segment.text for segment in segments).strip()

        try:
            text = await loop.run_in_executor(None, _transcribe)
        except Exception as e:
            raise APIConnectionError() from e

        return stt.SpeechEvent(
            type=SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(text=text, language=LanguageCode(lang or ""))],
        )
