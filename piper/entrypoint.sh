#!/bin/sh
set -e

VOICE="${PIPER_VOICE:-es_ES-davefx-medium}"
DATA_DIR="/data"

if [ ! -f "${DATA_DIR}/${VOICE}.onnx" ]; then
  echo "[piper] descargando voz '${VOICE}' en ${DATA_DIR} ..."
  python3 -m piper.download_voices "${VOICE}" --download-dir "${DATA_DIR}"
else
  echo "[piper] voz '${VOICE}' ya descargada, se omite la descarga"
fi

exec python3 -m piper.http_server \
  --host 0.0.0.0 \
  --port 5000 \
  -m "${DATA_DIR}/${VOICE}.onnx" \
  --data-dir "${DATA_DIR}"
