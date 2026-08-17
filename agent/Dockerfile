FROM python:3.11-slim

# ffmpeg: usado por faster-whisper/ctranslate2 para decodificar el WAV entrante
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Descarga en tiempo de build los pesos que livekit-agents necesita al iniciar
# (VAD Silero, turn-detector v1-mini) para no pagar esa latencia/red en cada arranque
# del contenedor. Ver: python -m livekit.agents download-files --help
RUN python3 -m livekit.agents download-files || true

CMD ["python3", "agent.py", "start"]
