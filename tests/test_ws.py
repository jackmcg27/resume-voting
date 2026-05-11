"""
Tests for socket.io event handlers.

Event handlers in app/events.py are plain async functions, so we call them
directly and mock sio.emit / sio.enter_room to avoid needing a running server.
"""
import pytest
from unittest.mock import ANY, AsyncMock

from app import socket as socket_module
from app.events import on_join_session, on_disconnect
from app.store import sessions


@pytest.fixture(autouse=True)
def mock_sio_methods(monkeypatch):
    monkeypatch.setattr(socket_module.sio, 'emit', AsyncMock())
    monkeypatch.setattr(socket_module.sio, 'enter_room', AsyncMock())


# ---------------------------------------------------------------------------
# join_session
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_join_session_adds_panelist(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    assert 'Alice' in sessions[session_code].panelists


@pytest.mark.anyio
async def test_join_session_enters_room(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    socket_module.sio.enter_room.assert_called_once_with('sid1', session_code)


@pytest.mark.anyio
async def test_join_session_broadcasts_state_to_room(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    socket_module.sio.emit.assert_called_with('state', ANY, room=session_code)


@pytest.mark.anyio
async def test_join_session_unknown_code_does_nothing():
    await on_join_session('sid1', {'code': 'NOPE99', 'name': 'Alice'})
    socket_module.sio.enter_room.assert_not_called()
    socket_module.sio.emit.assert_not_called()


@pytest.mark.anyio
async def test_join_session_no_name_sends_state_to_caller_only(session_code):
    """Moderator connects without a name — should receive state but not be listed as panelist."""
    await on_join_session('sid1', {'code': session_code, 'name': None})
    assert len(sessions[session_code].panelists) == 0
    socket_module.sio.emit.assert_called_once_with('state', ANY, to='sid1')


@pytest.mark.anyio
async def test_join_session_duplicate_name_not_re_registered(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    await on_join_session('sid2', {'code': session_code, 'name': 'Alice'})
    assert sessions[session_code].panelists['Alice'].client_id == 'sid1'


@pytest.mark.anyio
async def test_join_session_stores_sid_as_client_id(session_code):
    await on_join_session('sid-abc', {'code': session_code, 'name': 'Bob'})
    assert sessions[session_code].panelists['Bob'].client_id == 'sid-abc'


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_disconnect_removes_panelist(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    assert 'Alice' in sessions[session_code].panelists

    await on_disconnect('sid1')
    assert 'Alice' not in sessions[session_code].panelists


@pytest.mark.anyio
async def test_disconnect_broadcasts_after_removal(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    socket_module.sio.emit.reset_mock()

    await on_disconnect('sid1')
    socket_module.sio.emit.assert_called_with('state', ANY, room=session_code)


@pytest.mark.anyio
async def test_disconnect_unknown_sid_does_nothing(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    socket_module.sio.emit.reset_mock()

    await on_disconnect('sid-unknown')
    socket_module.sio.emit.assert_not_called()


@pytest.mark.anyio
async def test_disconnect_only_removes_matching_panelist(session_code):
    await on_join_session('sid1', {'code': session_code, 'name': 'Alice'})
    await on_join_session('sid2', {'code': session_code, 'name': 'Bob'})

    await on_disconnect('sid1')
    assert 'Alice' not in sessions[session_code].panelists
    assert 'Bob' in sessions[session_code].panelists
