#!/usr/bin/env bash
# Genera docker/livekit.yaml a partir de docker/livekit.yaml.template usando
# LIVEKIT_API_KEY / LIVEKIT_API_SECRET definidos en docker/.env.
# No requiere envsubst (no todas las imagenes lo tienen); usa sed, disponible
# en cualquier VPS Linux estandar.
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="docker/.env"
TEMPLATE="docker/livekit.yaml.template"
OUTPUT="docker/livekit.yaml"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: no existe $ENV_FILE. Copia docker/.env.example a docker/.env y completalo." >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

if [ -z "${LIVEKIT_API_KEY:-}" ] || [ -z "${LIVEKIT_API_SECRET:-}" ]; then
  echo "ERROR: LIVEKIT_API_KEY / LIVEKIT_API_SECRET no estan definidos en $ENV_FILE" >&2
  exit 1
fi

sed \
  -e "s|__LIVEKIT_API_KEY__|${LIVEKIT_API_KEY}|g" \
  -e "s|__LIVEKIT_API_SECRET__|${LIVEKIT_API_SECRET}|g" \
  "$TEMPLATE" > "$OUTPUT"

echo "Generado $OUTPUT"
echo "Siguiente paso: docker compose -f docker/docker-compose.yml up -d --build"
