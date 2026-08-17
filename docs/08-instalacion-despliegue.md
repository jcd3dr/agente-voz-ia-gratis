# Instalacion y despliegue en el VPS

Esta guia cubre las Etapas 2 a 5 del roadmap: llevar el codigo de este repositorio (carpetas `agent/`, `server/`, `piper/`, `docker/`, `web/`, `scripts/`) a un agente funcionando en tu VPS.

**Nota de verificacion:** todo el codigo de `agent/` esta escrito y verificado contra el codigo fuente real de `livekit-agents==1.6.10` (clonado y revisado linea por linea durante la construccion de este repo, no generado por analogia o memoria). Aun asi, **no se ha ejecutado de punta a punta contra un LiveKit Server real** porque este entorno de construccion no tenia acceso a tu VPS ni a PyPI para instalar y correr el stack completo. La Etapa 6 (pruebas) es precisamente para validar esto en tu infraestructura real y corregir lo que aparezca.

## 0. Requisitos previos

- VPS con Ubuntu 22.04+ que cumpla [`04-requisitos-vps.md`](./04-requisitos-vps.md) (minimo 4 vCPU / 8GB RAM, AVX2)
- Dos subdominios apuntando por DNS (registro A) a la IP del VPS — ver por que en la seccion 3
- Acceso SSH root/sudo al VPS

## 1. Clonar el repositorio en el VPS

```bash
git clone https://github.com/jcd3dr/agente-voz-ia-gratis.git
cd agente-voz-ia-gratis
```

## 2. Preparar el sistema (Etapa 2)

```bash
sudo bash scripts/01-setup-vps.sh
```

Instala Docker + el plugin `docker compose`, verifica AVX2/RAM/disco, y abre los puertos necesarios en `ufw` si esta presente.

## 3. Configurar dominios y secretos

Crea dos registros DNS tipo A apuntando a la IP del VPS:

```
livekit.tu-dominio.com   -> IP del VPS
agente.tu-dominio.com    -> IP del VPS
```

**Por que dos subdominios y no rutas bajo uno solo:** LiveKit Server expone su senalizacion WebSocket y su API interna en distintas rutas de su propio dominio; las guias de self-hosting verificadas (RamNode, comunidad LiveKit) proxyan siempre el **dominio completo** a `livekit-server`, sin mezclarlo con otras rutas. Intentar compartir un dominio entre LiveKit y la landing page via `/path` rompe la conexion del cliente. Con dos subdominios, cada uno se resuelve limpio.

Copia y completa el archivo de entorno:

```bash
cp docker/.env.example docker/.env
nano docker/.env   # completa LIVEKIT_DOMAIN, APP_DOMAIN, ACME_EMAIL, y genera un LIVEKIT_API_SECRET propio
```

Para generar un secreto aleatorio de 32+ caracteres:

```bash
openssl rand -hex 32
```

Renderiza la config de LiveKit a partir de tus variables:

```bash
bash scripts/02-render-config.sh
```

## 4. Levantar el stack

```bash
cd docker
docker compose up -d --build
```

Esto construye y arranca: `redis`, `livekit`, `ollama`, `piper` (descarga la voz espanola en el primer arranque), `token-server`, `caddy` (emite los certificados TLS automaticamente via Let's Encrypt), y `agent` (descarga los pesos de VAD/turn-detector en el build).

Verifica que todo este arriba:

```bash
docker compose ps
docker compose logs -f caddy      # confirma que emitio los certificados TLS sin errores
docker compose logs -f livekit
```

## 5. Descargar el modelo LLM (Etapa 4)

```bash
cd ..
bash scripts/03-pull-ollama-model.sh qwen2.5:7b-instruct
```

Puede tardar varios minutos segun el ancho de banda del VPS (el modelo pesa ~4.5GB).

## 6. Verificar el pipeline completo (Etapa 5-6)

```bash
docker compose -f docker/docker-compose.yml logs -f agent
```

Deberias ver al worker del agente registrarse contra `ws://livekit:7880` sin errores. Luego abre `https://agente.tu-dominio.com` en el navegador (Etapa 3), pulsa "Hablar con el agente", concede permiso de microfono, y habla.

### Si algo falla

| Sintoma | Causa probable | Donde mirar |
|---|---|---|
| El boton de la landing page no pide microfono | El dominio no tiene HTTPS valido todavia | `docker compose logs caddy` |
| "Error obteniendo el token" | `token-server` no levanto o CORS mal configurado | `docker compose logs token-server`, revisa `CORS_ALLOW_ORIGINS` en `.env` |
| Se conecta pero el agente nunca responde | El worker no se registro contra LiveKit, o Ollama no tiene el modelo descargado | `docker compose logs agent`, `docker compose exec ollama ollama list` |
| El agente transcribe mal / no entiende espanol | `AGENT_LANGUAGE`/`WHISPER_MODEL_SIZE` mal configurados, o audio del microfono con eco | `docker/.env`, probar `WHISPER_MODEL_SIZE=large-v3-turbo` si el VPS lo soporta |
| Piper no arranca | La voz configurada en `PIPER_VOICE` no existe con ese nombre exacto | `docker compose logs piper`; verificar nombres reales en https://huggingface.co/rhasspy/piper-voices |

Este es el punto exacto donde arranca la Etapa 6 del roadmap (medicion de latencia real y ajuste fino) — con el stack ya arriba, lo que sigue es afinar, no construir.
