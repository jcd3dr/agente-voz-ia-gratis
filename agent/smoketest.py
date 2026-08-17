"""Smoke test para el isolated-builder (jcd3dr/isolated-builder).

No requiere un LiveKit Server real: instancia directamente las piezas locales que
más recursos consumen al arrancar (el modelo de faster-whisper, que se descarga la
primera vez) y, si carga bien, levanta un HTTP mínimo en /health para que el
workflow pueda confirmarlo con curl. Objetivo: detectar temprano — en un runner
efímero de GitHub, sin tocar el VPS — si la construcción/arranque de esta imagen
se cuelga o consume demasiada memoria, antes de desplegarla en Coolify.
"""

from __future__ import annotations

import http.server
import os
import sys
import time

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

print(f"[smoketest] cargando faster-whisper modelo='{WHISPER_MODEL_SIZE}' ...", flush=True)
t0 = time.time()

from faster_whisper import WhisperModel  # noqa: E402

model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type=WHISPER_COMPUTE_TYPE,
    cpu_threads=2,
)

elapsed = time.time() - t0
print(f"[smoketest] modelo cargado OK en {elapsed:.1f}s", flush=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args) -> None:  # silencia el log por request
        pass


port = int(os.getenv("PORT", "8099"))
server = http.server.HTTPServer(("0.0.0.0", port), Handler)
print(f"[smoketest] sirviendo /health en :{port}", flush=True)
sys.stdout.flush()
server.serve_forever()
