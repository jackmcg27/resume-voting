import pytest


def test_connect_sends_initial_state(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "state"
        assert msg["session"]["code"] == session_code


def test_connect_to_unknown_session_is_rejected(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/NOPE99/c1") as ws:
            ws.receive_json()


def test_join_adds_panelist(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        ws.receive_json()  # initial state
        ws.send_json({"type": "join", "name": "Alice"})
        msg = ws.receive_json()  # broadcast after join
        assert "Alice" in msg["session"]["panelists"]


def test_join_empty_name_ignored(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        ws.receive_json()
        ws.send_json({"type": "join", "name": "   "})
        # No state broadcast expected — just close cleanly

    session = client.get(f"/api/sessions/{session_code}").json()
    assert session["panelists"] == []


def test_join_duplicate_name_ignored(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        ws.receive_json()
        ws.send_json({"type": "join", "name": "Alice"})
        ws.receive_json()  # broadcast for first join

        ws.send_json({"type": "join", "name": "Alice"})
        # Check while still connected — disconnect handler would remove Alice
        session = client.get(f"/api/sessions/{session_code}").json()
        assert session["panelists"].count("Alice") == 1


def test_ping_returns_pong(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        ws.receive_json()
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}


def test_disconnect_removes_panelist(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws:
        ws.receive_json()
        ws.send_json({"type": "join", "name": "Alice"})
        ws.receive_json()
    # Context manager closed — panelist should be removed on disconnect

    session = client.get(f"/api/sessions/{session_code}").json()
    assert "Alice" not in session["panelists"]


def test_multiple_clients_each_receive_broadcasts(client, session_code):
    with client.websocket_connect(f"/ws/{session_code}/c1") as ws1:
        ws1.receive_json()
        ws1.send_json({"type": "join", "name": "Alice"})
        ws1.receive_json()

        with client.websocket_connect(f"/ws/{session_code}/c2") as ws2:
            ws2.receive_json()  # initial state for c2
            ws2.send_json({"type": "join", "name": "Bob"})

            # Both clients get the broadcast
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()

    assert "Bob" in msg1["session"]["panelists"]
    assert "Bob" in msg2["session"]["panelists"]
