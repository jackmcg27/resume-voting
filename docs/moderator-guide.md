# Moderator Guide

The moderator controls the session from `/moderator`. This is the tab you share on the projected screen.

## 1. Create a session

Navigate to `http://<hostname>:8000/moderator`. You will be prompted to enter a session name — something descriptive like "Backend Engineer - May 2026" — so it's easy to identify later in the admin view. Click **Create Session**.

A 6-character session code (e.g. `C30G3V`) appears in the top bar alongside the full join URL. Share the code verbally or leave it visible on screen — panelists only need the code.

## 2. Add resumes to the queue

There are two ways to add resumes:

**Upload new PDFs** — click **Upload PDFs** in the sidebar and select one or more files. Each file is stored on the server and added to the pending queue immediately.

**Add from server** — click **Browse Server Files** to see all PDFs already on the server from previous sessions. Each file shows its original name and upload date. Click **Add** to drop it into the current queue without re-uploading.

Resumes can be added at any point during the session.

## 3. Watch panelists join

The **Panelists** section of the sidebar updates in real time as people join. You can see everyone who has connected before starting.

## 4. Open a resume

Click **Open** next to any pending resume. The PDF loads in the main panel on your screen and on every panelist's device simultaneously.

## 5. Open voting

Once the panel has had time to read the resume, click **Open Voting**.

Panelists now see the star-rating widget on their devices. A live counter in the toolbar shows how many have submitted (e.g. `3 / 5 submitted`) and a progress bar fills as votes come in.

Click **Close Voting** at any time to stop accepting new votes without revealing scores.

## 6. Reveal results

Click **Reveal Results** to show all scores and the average to everyone in the session at once.

The toolbar displays each panelist's score and the calculated average. The resume moves to **Reviewed** in the queue.

## 7. Advance to the next resume

Click **Next Resume** to open the next pending resume and repeat the process. You can also click **Open** on any specific item in the pending queue to jump to it out of order.

If you need to revisit a resume that has already been reviewed, click **Open** next to it in the **Reviewed** section of the queue. The PDF and scores will still be visible, and you can re-open voting if needed.

## 8. End the session

After the last resume is revealed, click **View Results** to clear the active resume and go to the leaderboard.

## 9. View the leaderboard

Click **Leaderboard (N)** in the top bar at any time to see the current standings without closing the active resume. Panelists continue to see whatever is on their screen while you browse the rankings. Click **Back to Session** to return.

The leaderboard is sorted by average score and updates after each reveal.

## 10. Export results

Click **Export CSV** at the bottom of the leaderboard to download a spreadsheet with every candidate's name, each panelist's individual score, and the average.

Results can also be exported at any time from the admin page at `/admin`.
