import random
import string
from collections import defaultdict
from typing import Dict

from fastapi import WebSocket

from .models import Session, session_view


sessions: Dict[str, Session] = {}
connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)


def generate_session_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


async def broadcast_state(code: str) -> None:
    session = sessions.get(code)
    if not session:
        return

    message = {"type": "state", "session": session_view(session)}
    dead = []

    for client_id, ws in connections[code].items():
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(client_id)

    for client_id in dead:
        connections[code].pop(client_id, None)
