# Admin Guide

The admin page gives a read-only overview of every session that has been created since the server started. It is intended for whoever runs the server — not for moderators or panelists.

## Accessing the admin page

Navigate to:

```
http://<hostname>:8000/admin
```

No login is required. Access is controlled by network — only machines that can reach the server can open this page.

## What it shows

Each row in the table represents one session and includes:

- **Session name** — the name entered when the session was created (e.g. "Backend Engineer - May 2026"), shown above the session code
- **Session code** — the 6-character code used to identify the session
- **Status** — one of:
  - *Idle* — session created but no resume is active
  - *In progress* — a resume is open and being reviewed
  - *Voting open* — panelists are currently submitting scores
  - *Complete* — all uploaded resumes have been reviewed and revealed
- **Panelists** — number of panelists who joined
- **Resumes** — total number of resumes in the queue
- **Reviewed** — how many have been revealed, with a percentage

## Actions

Both actions appear only once at least one resume has been reviewed.

**View Results / Hide Results** — expands an inline leaderboard directly in the admin table showing all reviewed candidates ranked by average score, with each panelist's individual scores as columns. Click again to collapse it.

**Export CSV** — downloads a spreadsheet with every candidate's name, each panelist's individual score, and the average.

## Limitations

Session data is held in memory. If the server restarts, all session history is lost. Export any results you need to keep before restarting the server.

## Refreshing

The admin page does not update automatically. Click **Refresh** in the top bar to reload the current state of all sessions.
