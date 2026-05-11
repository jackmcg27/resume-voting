import random
import string
from typing import Dict

from .models import Session, session_view

sessions: Dict[str, Session] = {}


def generate_session_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


async def broadcast_state(code: str) -> None:
    session = sessions.get(code)
    if not session:
        return

    from .socket import sio  # deferred to avoid circular import at module load
    await sio.emit('state', session_view(session), room=code)
