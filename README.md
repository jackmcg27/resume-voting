# Resume Screening App

A real-time, browser-based tool for structured resume reviews with a panel of interviewers. The moderator controls the session from one screen while panelists join independently on their own devices to read resumes and submit scores. Scores stay hidden until the moderator reveals them, keeping each vote uninfluenced.

Designed to run on a VM or any machine on an internal network — no cloud services, no database, no accounts required.

---

## How It Works

1. **Moderator** opens `/moderator`, creates a session, and gets a shareable code
2. **Panelists** open `/join` on their own devices and enter the code
3. Moderator uploads PDFs and opens them one at a time — the resume appears on every screen simultaneously
4. Moderator opens voting — each panelist submits a private 1-5 star score
5. Moderator watches the live submission count (`3 / 5 submitted`) and reveals when ready
6. All scores and the average appear on every screen at once
7. After all resumes, a ranked leaderboard is shown and results can be exported to CSV

---

## Features

- **Real-time sync** via WebSockets — resume changes, panelist joins, vote counts, and reveals all propagate instantly
- **Blind voting** — panelists cannot see each other's scores until the moderator reveals
- **Inline PDF rendering** via PDF.js — no downloads, works on phones and tablets
- **Live vote counter** — moderator sees `X / Y submitted` with a progress bar as votes come in
- **Ranked leaderboard** — candidates sorted by average score, accessible at any time mid-session
- **CSV export** — candidate name, each panelist's score, and average in one file
- **Server file browser** — re-use PDFs from previous sessions without re-uploading
- **Any number of panelists** — vote totals are calculated dynamically based on who's in the room
- **No login or accounts** — panelists just enter a name and session code
- **Persistent state** — session survives page refreshes; panelists reconnect automatically
- **Admin page** — view all sessions and export results from `/admin`
- **Configurable port** via `PORT` environment variable

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, WebSockets |
| Server | Uvicorn (ASGI) |
| Frontend | React, React Router |
| PDF rendering | PDF.js |
| Build tool | Vite |
| Package manager | uv (Python), npm (JS) |
| State | In-memory (no database) |
| Transport | Plain HTTP / WS (internal network) |

---

## Quick Start

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 18+

```powershell
# Install dependencies and build the frontend
uv sync
cd frontend && npm install && npm run build && cd ..

# Start the server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

| Route | Who uses it |
|---|---|
| `/moderator` | Moderator — controls the session |
| `/join` | Panelists — read resumes and vote |
| `/admin` | Admin — view all sessions and export results |

See [docs/getting-started.md](docs/getting-started.md) for full setup instructions including port configuration.

---

## Documentation

- [Getting Started](docs/getting-started.md) — installation, setup, and running the server
- [Moderator Guide](docs/moderator-guide.md) — running a screening session end to end
- [Panelist Guide](docs/panelist-guide.md) — joining a session and submitting scores
- [Admin Guide](docs/admin-guide.md) — viewing session history and exporting results

---

## Project Structure

```
resume-voting/
├── main.py                      # Entry point for uvicorn
├── pyproject.toml               # Python project config and dependencies (uv)
├── uploads/                     # Uploaded PDFs and metadata (created at runtime)
├── static/                      # Built frontend (created by npm run build)
├── app/
│   ├── config.py                # Port, upload dir, static dir
│   ├── models.py                # Data classes and serializers
│   ├── store.py                 # In-memory session state and WebSocket broadcast
│   ├── main.py                  # FastAPI app, middleware, router wiring
│   └── routers/
│       ├── admin.py             # GET /api/admin/sessions
│       ├── sessions.py          # Create and get sessions
│       ├── resumes.py           # Upload, add from server, activate, serve PDF
│       ├── voting.py            # Open, close, vote, reveal, export
│       └── ws.py                # WebSocket handler
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Admin.jsx        # Admin session overview
│   │   │   ├── Moderator.jsx    # Moderator control panel
│   │   │   └── Join.jsx         # Panelist join and voting view
│   │   ├── components/
│   │   │   ├── PDFViewer.jsx    # PDF.js canvas renderer
│   │   │   ├── StarRating.jsx   # 1-5 star input widget
│   │   │   └── Leaderboard.jsx  # Ranked results table
│   │   └── hooks/
│   │       └── useSessionWS.js  # WebSocket connection and state sync
│   └── vite.config.js
└── docs/
    ├── getting-started.md
    ├── moderator-guide.md
    ├── panelist-guide.md
    └── admin-guide.md
```
