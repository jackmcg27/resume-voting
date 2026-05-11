from .models import Panelist, session_view
from .socket import sio
from .store import broadcast_state, sessions


@sio.on('join_session')
async def on_join_session(sid, data):
    code = (data.get('code') or '').strip()
    session = sessions.get(code)
    if not session:
        return

    await sio.enter_room(sid, code)

    name = (data.get('name') or '').strip()
    if name and name not in session.panelists:
        session.panelists[name] = Panelist(name=name, client_id=sid)
        await broadcast_state(code)
    else:
        await sio.emit('state', session_view(session), to=sid)


@sio.on('disconnect')
async def on_disconnect(sid):
    for code, session in sessions.items():
        for name, panelist in list(session.panelists.items()):
            if panelist.client_id == sid:
                del session.panelists[name]
                await broadcast_state(code)
                return
