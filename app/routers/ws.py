import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models import Panelist, session_view
from ..store import sessions, connections, broadcast_state

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{code}/{client_id}")
async def websocket_endpoint(ws: WebSocket, code: str, client_id: str):
    session = sessions.get(code)
    if not session:
        await ws.close(code=4004)
        return

    await ws.accept()
    connections[code][client_id] = ws
    await ws.send_json({"type": "state", "session": session_view(session)})

    try:
        while True:
            raw = await ws.receive_text()
            message = json.loads(raw)

            if message.get("type") == "join":
                name = message.get("name", "").strip()
                if name and name not in session.panelists:
                    session.panelists[name] = Panelist(name=name, client_id=client_id)
                    await broadcast_state(code)

            elif message.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connections[code].pop(client_id, None)
        for name, panelist in list(session.panelists.items()):
            if panelist.client_id == client_id:
                del session.panelists[name]
                break
        await broadcast_state(code)
