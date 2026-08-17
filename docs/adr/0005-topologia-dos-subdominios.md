# 0005 — Topología de dos subdominios para exposición HTTP/WebRTC

## Status

Accepted

## Context

El proyecto tiene dos piezas que necesitan ser alcanzables por HTTP desde el navegador del usuario final: la landing page de validación (`web/`) y el servidor de tokens (`server/`). Ambas se despliegan como Applications separadas de Coolify. Se evaluó exponerlas bajo un solo dominio con distintas rutas (path-based routing, ej. `agente-voz.jcdcruz.com/token`) frente a dos subdominios independientes.

El enrutamiento por path bajo un solo dominio se intentó conceptualmente y se descartó por romper supuestos simples de Coolify/Traefik para dos Applications distintas sirviendo el mismo dominio raíz con reglas de path — cada Application de Coolify se gestiona con su propio FQDN de forma más directa y predecible.

Ver también `docs/04-requisitos-vps.md`, que ya documentaba la necesidad de dos subdominios como parte del dimensionamiento/networking original.

## Decision

Dos subdominios independientes, cada uno como su propia Coolify Application con su propio `fqdn`:

- Landing: `https://agente-voz.jcdcruz.com` (`base_directory=/web`)
- Token server: `https://agente-voz-token.jcdcruz.com` (`base_directory=/server`, puerto 8080)

El agent worker (`base_directory=/agent`) **no** lleva `fqdn` — no se expone por HTTP/Traefik, solo necesita alcanzar LiveKit Server, `ollama-api` y `kokoro-tts` por red interna.

`web/index.html` se actualizó para usar la URL absoluta del token-server (`TOKEN_SERVER_URL`) en vez de un fetch relativo `/token`, que solo funcionaría si ambos estuvieran servidos desde el mismo origen.

## Consequences

- Requiere dos registros DNS/FQDN configurados en Coolify en vez de uno.
- CORS: el token-server (`server/`) debe permitir origen cruzado desde `agente-voz.jcdcruz.com`, ya que la landing hace un `fetch` cross-origin al token-server — verificar que `server/` tenga esto configurado antes de dar la tarea 4.3 por terminada (no confirmado explícitamente en el código al momento de este ADR, queda como punto a revisar en esa tarea).
- Cambio de código relacionado: commit `d5142db` (`web/index.html`).
