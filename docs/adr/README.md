# Architecture Decision Records — índice

Convención: [Michael Nygard, "Documenting Architecture Decisions"](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). Un archivo por decisión técnica significativa y difícil de revertir. Nunca se edita un ADR ya aceptado para cambiar su decisión — si una decisión cambia, se escribe un ADR nuevo que la supersede, y el original se marca `Status: Superseded by ADR-00NN` (el contenido original queda intacto, es historia).

Formato de cada archivo: `NNNN-titulo-corto.md`, con secciones `Status`, `Context`, `Decision`, `Consequences`.

Las tareas en `docs/PLAN.md` citan estas decisiones por número ("per ADR-0002") en vez de repetirlas — si una tarea necesita el detalle de por qué se decidió algo, está aquí, no en `PLAN.md`.

| ADR | Título | Estado |
|---|---|---|
| [0001](0001-livekit-agents-como-orquestador.md) | LiveKit Agents + LiveKit Server como orquestador/transporte | Accepted |
| [0002](0002-seleccion-componentes-pipeline.md) | Selección de componentes del pipeline (VAD, turn detection, STT, LLM) | Accepted |
| [0003](0003-tts-piper.md) | TTS: Piper | Superseded by ADR-0004 |
| [0004](0004-tts-kokoro-fastapi-supersede-piper.md) | TTS: Kokoro-FastAPI (reemplaza Piper) | Accepted |
| [0005](0005-topologia-dos-subdominios.md) | Topología de dos subdominios para exposición HTTP/WebRTC | Accepted |
| [0006](0006-despliegue-coolify-nativo.md) | Despliegue Coolify-nativo, reutilizando servicios existentes del VPS | Accepted |
