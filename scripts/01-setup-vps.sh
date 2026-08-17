#!/usr/bin/env bash
# Preparacion inicial del VPS (Etapa 2). Ejecutar como root o con sudo en
# Ubuntu 22.04 LTS. Idempotente: se puede correr mas de una vez sin romper nada.
set -euo pipefail

echo "== Verificando requisitos de hardware =="
if ! lscpu | grep -qi avx2; then
  echo "ADVERTENCIA: el CPU no reporta soporte AVX2. Ollama y faster-whisper" >&2
  echo "cuantizados pueden no arrancar. Ver docs/04-requisitos-vps.md" >&2
fi
echo "Nucleos: $(nproc)"
free -h | grep -E "Mem|total"
df -h / | tail -1

echo "== Instalando Docker + Docker Compose plugin =="
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
else
  echo "Docker ya esta instalado, se omite"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: el plugin 'docker compose' no esta disponible tras la instalacion." >&2
  exit 1
fi

echo "== Abriendo puertos necesarios (ufw) =="
if command -v ufw >/dev/null 2>&1; then
  ufw allow 22/tcp    || true   # SSH — no lo cierres sin verificar tu sesion actual
  ufw allow 80/tcp    || true   # Caddy: HTTP (redirige a HTTPS)
  ufw allow 443/tcp   || true   # Caddy: HTTPS
  ufw allow 7881/tcp  || true   # LiveKit: RTC over TCP (fallback)
  ufw allow 50000:60000/udp || true  # LiveKit: rango RTP de medios WebRTC
  echo "Reglas de ufw aplicadas. Revisa 'ufw status' antes de 'ufw enable'."
else
  echo "ufw no encontrado; abre manualmente 80/tcp, 443/tcp, 7881/tcp y 50000-60000/udp"
fi

echo "== Listo. Siguiente paso: scripts/02-render-config.sh =="
