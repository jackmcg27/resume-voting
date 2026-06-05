# Getting Started

The server runs on an Ubuntu VM. All commands below are run on that VM over SSH or directly in a terminal.

## Prerequisites

Install the required tools on the VM if they are not already present.

**Python 3.11+ and uv**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

**Node.js 18+**

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Bun** (required for the auth server)

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
```

## GitLab OAuth app

The admin page is protected by GitLab OAuth. Before setting up the server you need a GitLab OAuth application.

1. Go to **GitLab → User Settings → Applications** (or a group's **Settings → Applications** for a group-owned app)
2. Set the **Redirect URI** to:
   ```
   http://resume-voting-vm:8000/api/auth/callback/gitlab
   ```
   Replace `resume-voting-vm` with your VM's hostname or IP address. If you're running behind nginx on port 80, omit `:8000`.
3. Enable the `read_api` and `openid` scopes (the `api` scope is needed to check group membership)
4. Save and note the **Application ID** and **Secret**

## First-time setup

Clone the repo and run the following from the project root.

**1. Install Python dependencies**

```bash
uv sync
```

**2. Install auth server dependencies**

```bash
cd auth
bun install
cd ..
```

**3. Configure the auth server**

```bash
cp auth/.env.example auth/.env
```

Edit `auth/.env` and fill in:

```env
# Generate with: openssl rand -base64 32
BETTER_AUTH_SECRET=<long-random-string>

# URL where the auth server is reachable — used to build OAuth callback URLs
BETTER_AUTH_URL=http://resume-voting-vm:3001

# From your GitLab OAuth application
GITLAB_CLIENT_ID=<application-id>
GITLAB_CLIENT_SECRET=<secret>

# GitLab group path or numeric ID — only members of this group can access /admin
GITLAB_GROUP=your-org/your-group

# For self-hosted GitLab, uncomment:
# GITLAB_URL=https://gitlab.example.com
```

**4. Create the auth database**

```bash
cd auth
bun run migrate
cd ..
```

This creates `auth/auth.db` (SQLite) with the tables Better Auth needs for sessions and accounts.

**5. Build the frontend**

```bash
cd frontend
npm install
npm run build
cd ..
```

This compiles the React app into `static/`, which FastAPI serves automatically.

## Running the servers

The app requires two processes: the auth server and the FastAPI server.

**Auth server** (port 3001):

```bash
cd auth && bun run start
```

**App server** (port 8000):

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The app is now available at `http://localhost:8000` on the VM and at the VM's hostname or IP from other devices on the network.

## Deploying on the network

Both servers bind to all interfaces, so they accept connections from any device on the network as soon as they start.

### Finding the machine's address

```bash
hostname
```

If your organisation's DNS resolves VM hostnames, panelists can use it directly:

```
http://resume-voting-vm:8000
```

If DNS is not available, use the IP address instead:

```bash
hostname -I | awk '{print $1}'
```

Then share the URL in the form:

```
http://192.168.1.42:8000
```

### What to share with panelists

Tell panelists to open a browser on their own device and go to:

```
http://resume-voting-vm:8000/join
```

The full join URL is also shown on the moderator screen next to the session code.

### Firewall

Ubuntu's firewall is usually inactive by default. If devices cannot reach the server, check whether `ufw` is enabled and open the ports:

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 3001/tcp
sudo ufw reload
```

To remove the rules later:

```bash
sudo ufw delete allow 8000/tcp
sudo ufw delete allow 3001/tcp
```

### Keeping the servers running

For a session where you just need the servers up while you're connected, use `nohup` so they keep running if your SSH connection drops:

```bash
# Auth server
nohup bash -c 'cd /path/to/resume-voting/auth && bun run start' &> auth.log &
echo $! > auth.pid

# App server
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &> server.log &
echo $! > server.pid
```

To stop them:

```bash
kill $(cat auth.pid) $(cat server.pid)
```

For a longer-lived deployment where the servers should survive reboots, set them up as systemd services.

Create `/etc/systemd/system/resume-voting-auth.service`:

```ini
[Unit]
Description=Resume Voting Auth Server
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/resume-voting/auth
ExecStart=/home/<your-username>/.bun/bin/bun run start
Restart=on-failure
EnvironmentFile=/path/to/resume-voting/auth/.env

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/resume-voting.service`:

```ini
[Unit]
Description=Resume Voting App Server
After=network.target resume-voting-auth.service

[Service]
User=<your-username>
WorkingDirectory=/path/to/resume-voting
ExecStart=/path/to/resume-voting/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start both:

```bash
sudo systemctl daemon-reload
sudo systemctl enable resume-voting-auth resume-voting
sudo systemctl start resume-voting-auth resume-voting
```

Check logs:

```bash
sudo journalctl -u resume-voting-auth -f
sudo journalctl -u resume-voting -f
```

## Changing the port

```bash
PORT=9000 uv run uvicorn app.main:app --host 0.0.0.0 --port 9000
```

If you change port 8000, also update the GitLab OAuth redirect URI and `BETTER_AUTH_URL` in `auth/.env`.

## Subsequent starts

After first-time setup, only the two server start commands are needed — no reinstalling or rebuilding unless the code changes.

## Rebuilding the frontend (after code changes only)

```bash
cd frontend
npm run build
cd ..
```
