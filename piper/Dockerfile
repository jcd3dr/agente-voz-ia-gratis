# Piper TTS local, autoalojado. Usa el fork activamente mantenido
# OHF-Voice/piper1-gpl (paquete PyPI "piper-tts"), licencia GPL-3.0-or-later.
# El "rhasspy/piper" original (MIT) esta archivado desde 2025 y ya no recibe updates.
FROM python:3.11-slim

RUN pip install --no-cache-dir "piper-tts[http]"

WORKDIR /data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
