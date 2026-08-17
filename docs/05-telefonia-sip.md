# Telefonía / SIP: el único componente que puede no ser 100% gratis

## Distinción importante

Hay dos formas de que un usuario "hable" con el agente:

1. **WebRTC (navegador o app)**: el usuario abre una página web o app, el micrófono se captura vía WebRTC y se conecta directo al LiveKit Server. **Esto es 100% gratis** — no hay número de teléfono, no hay carrier, no hay costo por minuto. Todo el tráfico corre sobre la infraestructura propia del VPS.

2. **PSTN real (llamar a un número de teléfono)**: para que alguien marque un número real desde su celular o teléfono fijo y llegue al agente, se necesita un **troncal SIP (SIP trunk)** que traduzca la red telefónica tradicional a SIP/WebRTC. Esto es infraestructura de telecomunicaciones real y, salvo excepciones puntuales, **no es gratuita de forma sostenida**.

## Por qué no es gratis

Un troncal SIP requiere que un proveedor de telecomunicaciones (Twilio, Telnyx, un carrier local, etc.) le asigne un número de teléfono (DID) y curse las llamadas hacia la red telefónica pública. Eso tiene costo operativo real para el proveedor (interconexión con carriers), por lo que ningún proveedor serio lo regala indefinidamente. Existen capas gratuitas de prueba (créditos iniciales de Twilio/Telnyx), pero se agotan.

## Opciones si se quiere agregar telefonía real más adelante

| Opción | Costo aproximado | Nota |
|---|---|---|
| LiveKit SIP + Twilio Elastic SIP Trunking | ~$1/mes por número + $0.0085/min saliente (EE.UU., referencia) | El más simple de integrar con LiveKit (soporte oficial) |
| FreeSWITCH o Asterisk propio + troncal mayorista | Variable, requiere troncal mayorista igualmente | Solo cambia dónde vive el PBX, no elimina el costo del troncal |
| Servicios VoIP con capa gratuita limitada | $0 dentro de cupo mensual bajo | Útil solo para pruebas, no para uso sostenido |

## Recomendación para este proyecto

Fase 1 del proyecto (y del video): **quedarse en WebRTC**, que cubre el 100% del objetivo de "agente de voz conversacional gratis" sin comprometer esa promesa. La telefonía PSTN se documenta aquí como una extensión futura opcional, explícitamente fuera del alcance de "gratis", para no generar expectativas falsas en la audiencia del video.
