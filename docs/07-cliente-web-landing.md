# Cliente de validación: landing page web

## De dónde sale la voz del agente (flujo técnico exacto)

1. El LLM (Ollama/Qwen2.5-7B) genera texto en streaming, token a token.
2. Piper recibe ese texto (por frases/chunks, no espera el mensaje completo) y sintetiza audio PCM localmente, en el propio VPS. No hay ningún archivo pregrabado: cada respuesta se genera en el momento, es audio sintético en tiempo real.
3. El LiveKit Agent worker publica ese audio como un track de audio dentro de la sala (`room`) de LiveKit, codificado en Opus.
4. LiveKit Server retransmite ese track vía WebRTC hasta el navegador del usuario.
5. El navegador reproduce el audio por el altavoz/auriculares del dispositivo, a través de un elemento `<audio>` que el LiveKit Client SDK gestiona automáticamente al suscribirse al track remoto.

Es decir: **la voz "sale" del VPS, viaja como stream WebRTC, y se reproduce en el hardware de audio del usuario** — el mismo mecanismo que una videollamada, solo que uno de los participantes es el agente.

## Por qué la landing page es el cliente correcto para v1

Confirmado: es la decisión correcta, y ya estaba implícita en la arquitectura (WebRTC = gratis, sin PSTN — ver [`05-telefonia-sip.md`](./05-telefonia-sip.md)). Una landing page mínima con el LiveKit Client SDK es, de hecho, el cliente de referencia que LiveKit espera para cualquier integración web — no es un atajo de prueba, es el mismo mecanismo que usaría un producto final.

Corrección de roadmap: en vez de dejar el cliente web solo para la Etapa 7 (demo de cierre), se adelanta como **herramienta de validación desde la Etapa 3** — es la única forma real de comprobar que el pipeline completo funciona de punta a punta en cada etapa siguiente.

## Componentes mínimos de la landing page

| Pieza | Qué hace | Gratis |
|---|---|---|
| LiveKit Client SDK (JS, vía CDN o npm) | Conecta el navegador a la sala LiveKit por WebRTC | Sí, Apache-2.0 |
| Servidor de tokens (endpoint pequeño en el backend del VPS) | Genera un JWT firmado con `LIVEKIT_API_KEY`/`LIVEKIT_API_SECRET` que autoriza al navegador a entrar a una sala específica | Sí, se aloja junto al resto del stack |
| HTML + botón "Hablar" | Pide permiso de micrófono (`getUserMedia`), conecta a la sala con el token, publica el audio del micrófono y se suscribe al audio del agente | Sí |
| HTTPS/TLS en el dominio | Obligatorio: los navegadores bloquean `getUserMedia` fuera de `localhost` si no es un contexto seguro (HTTPS) | Sí, con Let's Encrypt (ya contemplado en requisitos de VPS) |

No se requiere React ni build tools para v1 — un solo archivo HTML con el SDK vía `<script>` y JS vanilla es suficiente para validar el pipeline completo. Frameworks (React + `@livekit/components-react`) quedan como mejora para una fase posterior si la landing evoluciona a producto.

## Flujo de uso en la landing page

1. Usuario entra a la URL del VPS (dominio con HTTPS).
2. Clic en "Hablar con el agente" → el navegador pide permiso de micrófono.
3. El frontend pide un token al backend (`POST /token`), se conecta a la sala de LiveKit.
4. El worker del agente (que ya está escuchando esa sala) arranca el pipeline VAD → STT → LLM → TTS.
5. El usuario habla, ve/escucha la respuesta del agente en tiempo real, puede interrumpirlo (barge-in).

Esta landing page es intencionalmente desechable/mínima para v1: su único propósito es demostrar que el stack completo funciona de punta a punta con una interfaz humana real, no ser un producto pulido.
