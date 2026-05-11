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

## First-time setup

Clone the repo and run the following from the project root:

**1. Install Python dependencies**

```bash
uv sync
```

**2. Build the frontend**

```bash
cd frontend
npm install
npm run build
cd ..
```

This compiles the React app into `static/`, which FastAPI serves automatically.

**3. Start the server**

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The app is now available at `http://localhost:8000` on the VM and at the VM's hostname or IP address from other devices on the network.

## Deploying on the network

The server binds to `0.0.0.0`, so it accepts connections from any device on the network as soon as it starts.

### Finding the machine's address

```bash
hostname
```

If your organization's DNS resolves VM hostnames, panelists can use it directly:

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

The full join URL is also shown on the moderator screen next to the session code, so you can leave it visible on the projected display.

### Firewall

Ubuntu's firewall is usually inactive by default. If panelists cannot reach the server, check whether `ufw` is enabled and open the port:

```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

To remove the rule later:

```bash
sudo ufw delete allow 8000/tcp
```

### Keeping the server running

For a session where you just need the server up while you're connected, use `nohup` so it keeps running if your SSH connection drops:

```bash
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &> server.log &
echo $! > server.pid
```

To stop it:

```bash
kill $(cat server.pid)
```

For a longer-lived deployment where the server should survive reboots, set it up as a systemd service. Create `/etc/systemd/system/resume-voting.service`:

```ini
[Unit]
Description=Resume Voting
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/resume-voting
ExecStart=/path/to/resume-voting/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable resume-voting
sudo systemctl start resume-voting
```

Check the logs:

```bash
sudo journalctl -u resume-voting -f
```

## Changing the port

```bash
PORT=9000 uv run uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## Subsequent starts

After the first-time setup, only the server start command is needed — no reinstalling or rebuilding unless the code changes.

## Rebuilding the frontend (after code changes only)

```bash
cd frontend
npm run build
cd ..
```
