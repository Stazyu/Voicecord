import asyncio
import json
import os
import sys

import requests
import websockets
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATUS = os.getenv("STATUS", "online").lower()  # online / dnd / idle
SELF_MUTE = os.getenv("SELF_MUTE", "true").lower() == "true"
SELF_DEAF = os.getenv("SELF_DEAF", "false").lower() == "true"

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


async def heartbeat(ws, interval):
    while True:
        await asyncio.sleep(interval / 1000)
        await ws.send(json.dumps({"op": 1, "d": None}))


async def main():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri, max_size=10 * 1024 * 1024) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

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
