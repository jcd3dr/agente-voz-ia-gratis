"""TTS local hablando por HTTP con un servidor Piper (`piper.http_server`) autoalojado.

Piper corre en su propio contenedor (ver `piper/Dockerfile`), expuesto solo en la red
interna de Docker. Este plugin implementa la interfaz batch (`synthesize` ->
`ChunkedStream`) de `livekit.agents.tts.TTS`, siguiendo el mismo patron que el plugin
oficial `livekit-plugins-spitch` (clase TTS/ChunkedStream), verificado contra el
codigo fuente real de livekit-agents==1.6.10.

Nota de licencia: el fork activamente mantenido de Piper (OHF-Voice/piper1-gpl,
paquete PyPI `piper-tts`) es GPL-3.0-or-later, no MIT (el `rhasspy/piper` original,
MIT, esta archivado desde 2025). Ver docs/02-componentes.md para el detalle.
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

# 22050 Hz es la frecuencia de muestreo estandar de la mayoria de las voces Piper
# (incluida es_ES-davefx-medium). Si se usa otra voz, verificar su *.onnx.json
# (clave "audio"."sample_rate") y ajustar PIPER_SAMPLE_RATE.
SAMPLE_RATE = int(os.getenv("PIPER_SAMPLE_RATE", "22050"))
NUM_CHANNELS = 1
MIME_TYPE = "audio/wav"


@dataclass
class _TTSOptions:
    base_url: str


class PiperTTS(tts.TTS):
    def __init__(self, *, base_url: str = "http://piper:5000") -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _TTSOptions(base_url=base_url.rstrip("/"))
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10))

    @property
    def model(self) -> str:
        return "piper"

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
        tts: PiperTTS,
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
                f"{self._opts.base_url}/synthesize",
                json={"text": self.input_text},
                timeout=httpx.Timeout(30, connect=self._conn_options.timeout),
            )
            resp.raise_for_status()

            # Piper devuelve un WAV completo (con cabecera); el AudioEmitter lo
            # decodifica automaticamente al recibir mime_type != audio/pcm.
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
