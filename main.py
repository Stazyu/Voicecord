import asyncio
import json
import os
import sys

import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import websockets
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# Get the API URL from the environment variable

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATUS = os.getenv("STATUS", "online").lower()  # online / dnd / idle
SELF_MUTE = os.getenv("SELF_MUTE", "true").lower() == "true"
SELF_DEAF = os.getenv("SELF_DEAF", "false").lower() == "true"

# Health check server settings
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
HEALTH_HOST = os.getenv("HEALTH_HOST", "0.0.0.0")
HEALTH_STALE_AFTER = int(os.getenv("HEALTH_STALE_AFTER", "60"))  # seconds

# Tracks the last time the Discord gateway was successfully reached.
# Updated by the heartbeat task. Read by the HTTP health endpoint.
_last_heartbeat_ts = 0.0
_health_lock = threading.Lock()

API = "https://discord.com/api/v10"

REQUIRED_VARS = {
    "DISCORD_TOKEN": TOKEN,
    "GUILD_ID": GUILD_ID,
    "CHANNEL_ID": CHANNEL_ID,
}

missing = [name for name, value in REQUIRED_VARS.items() if not value]
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}")
    print("Set them in a .env file or pass them via the container environment.")
    sys.exit(1)

if STATUS not in ("online", "dnd", "idle"):
    print(f"Invalid STATUS '{STATUS}'. Must be one of: online, dnd, idle.")
    sys.exit(1)

res = requests.get(f"{API}/users/@me", headers={"Authorization": TOKEN})
if res.status_code != 200:
    print("Invalid token!")
    sys.exit(1)

user = res.json()
print(f"Logged in as {user['username']} ({user['id']})!")

# Start the HTTP health endpoint so Docker can probe liveness.
_start_health_server()


async def heartbeat(ws, interval):
    global _last_heartbeat_ts
    while True:
        await asyncio.sleep(interval / 1000)
        await ws.send(json.dumps({"op": 1, "d": None}))
        with _health_lock:
            _last_heartbeat_ts = time.time()


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - http.server API
        with _health_lock:
            last = _last_heartbeat_ts
        age = time.time() - last if last else float("inf")
        healthy = last > 0 and age <= HEALTH_STALE_AFTER
        body = json.dumps({
            "status": "ok" if healthy else "stale",
            "last_heartbeat_age_seconds": None if last == 0 else round(age, 2),
            "stale_threshold_seconds": HEALTH_STALE_AFTER,
        }).encode("utf-8")
        self.send_response(200 if healthy else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # silence default access log
        return


def _start_health_server() -> None:
    server = HTTPServer((HEALTH_HOST, HEALTH_PORT), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    print(f"Health endpoint listening on http://{HEALTH_HOST}:{HEALTH_PORT}/health")


async def main():
    global _last_heartbeat_ts
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri, max_size=10 * 1024 * 1024) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        # Mark gateway as reachable as soon as we get the HELLO frame.
        with _health_lock:
            _last_heartbeat_ts = time.time()

        asyncio.create_task(heartbeat(ws, heartbeat_interval))

        print("Sending ready event...")

        await ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {
                    "$os": "linux",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": STATUS,
                    "afk": False
                }
            }
        }))

        while True:
            event = json.loads(await ws.recv())
            if event.get("t") == "READY":
                break

        await ws.send(json.dumps({
            "op": 4,
            "d": {
                "guild_id": GUILD_ID,
                "channel_id": CHANNEL_ID,
                "self_mute": SELF_MUTE,
                "self_deaf": SELF_DEAF
            }
        }))

        print("Joined the voice channel!")

        while True:
            try:
                msg = await ws.recv()
            except Exception:
                print("Disconnected, reconnecting...")
                break


async def run():
    while True:
        try:
            await main()
        except Exception as e:
            print("Error: ", e)
            await asyncio.sleep(5)


asyncio.run(run())
