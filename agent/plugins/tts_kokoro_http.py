"""TTS hablando por HTTP con Kokoro-FastAPI (`ghcr.io/remsky/kokoro-fastapi-cpu`),
ya desplegado en el VPS del usuario vía Coolify (servicio `kokoro-tts`) — se reutiliza
en lugar de desplegar un Piper nuevo.

Kokoro-FastAPI expone un endpoint compatible con la API de OpenAI
(`POST /v1/audio/speech`), pero solo el modo "bytes completos" (como los modelos
antiguos `tts-1`/`tts-1-hd` de OpenAI), no el modo SSE de streaming por eventos que
usa el plugin oficial `livekit-plugins-openai` para sus modelos por defecto
(`gpt-4o-mini-tts`, ver `tts.py` del plugin oficial, clase `SSEChunkedStream`).
Forzar el plugin oficial con `model="tts-1"` dependería de que Kokoro ignore ese
nombre de modelo sin documentarlo — no verificado. Por eso este plugin implementa
la interfaz batch (`synthesize` -> `ChunkedStream`) directamente por HTTP, igual
que `tts_piper_http.py`, siguiendo el mismo patrón verificado contra el código
fuente real de livekit-agents==1.6.10 (clase `livekit-plugins-spitch`).

Voces en español: prefijo `ef_` (ej. `ef_dora`). Ver
https://github.com/remsky/Kokoro-FastAPI (README, sección de voces) — verificado
por fetch directo al README el 2026-08-17.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import httpx

from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tts,
)

# Kokoro no publica oficialmente su sample rate nativo en el README consultado.
# No es crítico: livekit-agents decodifica el WAV recibido y RE-MUESTREA al valor
# declarado aquí en AudioEmitter.initialize() (ver codecs.AudioStreamDecoder en
# livekit-agents/livekit/agents/tts/tts.py) — 24000 Hz es el valor usado por los
# modelos TTS de OpenAI y un target razonable para voz.
SAMPLE_RATE = int(os.getenv("KOKORO_SAMPLE_RATE", "24000"))
NUM_CHANNELS = 1
MIME_TYPE = "audio/wav"


@dataclass
class _TTSOptions:
    base_url: str
    voice: str
    model: str


class KokoroTTS(tts.TTS):
    def __init__(
        self,
        *,
        base_url: str = "http://kokoro-tts:8880",
        voice: str = "ef_dora",
        model: str = "kokoro",
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _TTSOptions(base_url=base_url.rstrip("/"), voice=voice, model=model)
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10))

    @property
    def model(self) -> str:
        return self._opts.model

    @property
    def provider(self) -> str:
        return "local"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> ChunkedStream:
        return ChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            opts=self._opts,
            client=self._client,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class ChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: KokoroTTS,
        input_text: str,
        conn_options: APIConnectOptions,
        opts: _TTSOptions,
        client: httpx.AsyncClient,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._opts = opts
        self._client = client

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        request_id = uuid.uuid4().hex[:12]
        try:
            resp = await self._client.post(
                f"{self._opts.base_url}/v1/audio/speech",
                json={
                    "model": self._opts.model,
                    "voice": self._opts.voice,
                    "input": self.input_text,
                    "response_format": "wav",
                },
                timeout=httpx.Timeout(30, connect=self._conn_options.timeout),
            )
            resp.raise_for_status()

            output_emitter.initialize(
                request_id=request_id,
                sample_rate=SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
                mime_type=MIME_TYPE,
            )
            output_emitter.push(resp.content)
            output_emitter.flush()

        except httpx.TimeoutException:
            raise APITimeoutError() from None
        except httpx.HTTPStatusError as e:
            raise APIStatusError(
                str(e),
                status_code=e.response.status_code,
                request_id=request_id,
                body=e.response.text,
            ) from None
        except Exception as e:
            raise APIConnectionError() from e
