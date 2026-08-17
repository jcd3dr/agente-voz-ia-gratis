#!/usr/bin/env bash
# Descarga el modelo LLM dentro del contenedor de Ollama ya corriendo.
# Ejecutar despues de "docker compose up -d" (Etapa 4).
set -euo pipefail

cd "$(dirname "$0")/.."

MODEL="${1:-qwen2.5:7b-instruct}"

echo "Descargando modelo Ollama: ${MODEL} (puede tardar varios minutos)..."
docker compose -f docker/docker-compose.yml exec ollama ollama pull "${MODEL}"
echo "Listo. Modelos instalados:"
docker compose -f docker/docker-compose.yml exec ollama ollama list
