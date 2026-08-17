"""Servidor de tokens: emite JWT de LiveKit para que la landing page pueda unirse
a una sala. Nunca expone LIVEKIT_API_SECRET al navegador.

`AccessToken`/`VideoGrants` verificados contra el codigo fuente real de
livekit-api (github.com/livekit/python-sdks, livekit-api/livekit/api/access_token.py).
"""

from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel

LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
LIVEKIT_URL = os.environ["LIVEKIT_URL_PUBLIC"]  # wss://tu-dominio, para el navegador
ROOM_NAME = os.getenv("AGENT_ROOM_NAME", "agente-voz-demo")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")

app = FastAPI(title="agente-voz-ia-gratis: token server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str
    identity: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/token", response_model=TokenResponse)
def issue_token() -> TokenResponse:
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LIVEKIT_API_KEY/SECRET no configurados")

    identity = f"usuario-{uuid.uuid4().hex[:8]}"

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(VideoGrants(room_join=True, room=ROOM_NAME))
        .to_jwt()
    )

    return TokenResponse(token=token, url=LIVEKIT_URL, room=ROOM_NAME, identity=identity)
