# 0006 — Despliegue Coolify-nativo, reutilizando servicios existentes del VPS

## Status

Accepted

## Context

El despliegue original documentado en `docs/08-instalacion-despliegue.md` asume acceso manual por SSH y `docker-compose` directo sobre el VPS. El VPS real del usuario está gestionado por **Coolify** (PaaS self-hosted), que ya administra otros servicios del mismo dueño — notablemente `ollama-api` y `kokoro-tts`, reutilizados por este proyecto (no-negociable #3, ver ADR-0002 y ADR-0004).

Arquitectura de Coolify verificada contra la documentación real (`search_docs`/`WebFetch`, no asumida): cada recurso "Service" (docker-compose) se despliega en su propia red Docker privada nombrada por el UUID de ese recurso, no una red compartida por defecto. El toggle "Connect to Predefined Network" (solo disponible en la UI, no expuesto por la herramienta `coolify-mcp` usada en este proyecto) es el mecanismo oficialmente soportado por Coolify para unir un recurso a la red compartida `coolify`. La documentación de Coolify desaconseja declarar redes externas/custom manualmente en una Application tipo "Docker Compose" por riesgo de 504 (aislamiento respecto al proxy Traefik) — advertencia que aplica a servicios expuestos por FQDN, no necesariamente al agent worker (sin `fqdn`, no pasa por Traefik). Este matiz no está confirmado end-to-end todavía (ver `docs/PLAN.md`, tarea 4.4, `TODO`).

## Decision

Desplegar usando los recursos nativos de Coolify en vez de scripts SSH manuales:

- **Applications** (build desde GitHub, este repo) para `token-server` (`base_directory=/server`), `agent` worker (`base_directory=/agent`) y `web` landing (`base_directory=/web`) — ver ADR-0005 para la topología de FQDNs.
- **Service** (docker-compose) para la infraestructura propia del proyecto que no existe ya en el VPS: LiveKit Server + Redis (nombre de recurso "voz-ia-infra").
- Reutilizar, sin duplicar, los Services ya vivos `ollama-api` y `kokoro-tts` para LLM y TTS respectivamente.
- El script de despliegue manual (`scripts/`) y la guía `docs/08-instalacion-despliegue.md` **no se eliminan** — quedan como alternativa documentada para quien no use Coolify, marcados como parcialmente superseded por este ADR en lo que respecta al despliegue real usado en este proyecto.

## Consequences

- El despliegue real depende de la disponibilidad y estabilidad del conector `coolify-mcp` usado por los agentes de esta serie — si no está disponible, un agente sin ese conector debe operar manualmente desde la UI de Coolify siguiendo los mismos pasos (ver `AGENTS.md`, sección "Agnosticismo de herramienta").
- **Riesgo no resuelto al momento de este ADR:** el Service "voz-ia-infra" (LiveKit Server + Redis) no ha logrado arrancar sano en el VPS real tras múltiples intentos — ver `docs/PLAN.md`, tarea 4.1, `BLOCKED`. Esta decisión de arquitectura (usar Coolify nativo) no está en duda por ese bloqueo; el bloqueo es operativo (recursos del VPS / config del contenedor LiveKit), no arquitectónico.
- La resolución exacta del networking interno entre el agent worker y `ollama-api`/`kokoro-tts` queda pendiente de validación real (tarea 4.4).
