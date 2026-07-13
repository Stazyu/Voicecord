<div id="Phantom" align="center">
    <h1>Voicecord</h1>
    <p>Make Your Discord Account 24/7 On Voice Channels!</p>
    <img src="https://i.imgur.com/Pzu4u0S.png" height="100">
</div>

<br>

<p align="center">
<b>⭐ Feel free to star the repository if this helped you!</b>
</p>

## Disclaimer
By using this code, you are automating your Discord Account. This is against Discord's Terms of Service and Community Guidelines. If not used properly, your account(s) might get suspended or terminated by Discord. I, the developer, is not responsible for any consequences that may arise from the use of this code. Use this software at your own risk and responsibility. Learn more about <a href="https://discord.com/terms">Discord's Terms of Service</a> and <a href="https://discord.com/guidelines">Community Guidelines</a> here.
#### This repository is in no way affiliated with, authorized, maintained, sponsored or endorsed by Discord Inc. (discord.com) or any of its affiliates or subsidiaries.

## Warning
**DO <ins>NOT</ins> GIVE YOUR DISCORD TOKENS TO ANYONE.**
#### Giving your token to someone else will give them the ability to log into your account without the password or 2FA.

---

## ✨ Features:
- Secure [🔒]
- Supports Stage Channels
- Account will stay 24/7 online
- Supports all three status modes (Online, Idle, Do Not Disturb)
- Can be used on any platform that supports [Python](https://python.org)

---

## 🔎 Obtaining Your Token
You will need an user token inorder to use this code. You can obtain it by doing the following:
1. Logging in to your discord account
2. Pressing `Ctrl+Shift+I` to open Chrome Developer Tools
3. Go to the `Network` Tab
4. Keep it open and refresh the page
5. Type `/api` in the filter search box
6. Click the entry that has `science` as the `Name`
7. On the sub-menu, go to `Headers`
8. Scroll down till you see an entry named `Authorization`. Copy the line next to it.
9. This is your token. <ins>**DO NOT GIVE IT TO ANYONE**</ins>.

---

## 🛠️ Installation

### Option A — Local (Python)

1. Install [Python](https://python.org/downloads) on your machine (Make sure you add it to [PATH](https://i.imgur.com/Ukl6HdQ.png))
2. Download the repository and extract it
3. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN`, `GUILD_ID`, and `CHANNEL_ID` (and optionally `STATUS`, `SELF_MUTE`, `SELF_DEAF`)
4. Open a command prompt inside the folder and run `pip install -r requirements.txt`
5. Start the bot with `python main.py`

### Option B — Docker (recommended for 24/7 hosting)

1. Install [Docker](https://www.docker.com/get-started/) on your host machine
2. Copy `.env.example` to `.env` and fill in your token, guild ID, and channel ID
3. Build the image:

   ```bash
   docker build -t voicecord .
   ```

4. Run the container (loads variables from `.env` automatically):

   ```bash
   docker run -d --name voicecord --restart unless-stopped --env-file .env voicecord
   ```

   Or pass variables inline:

   ```bash
   docker run -d --name voicecord --restart unless-stopped \
     -e DISCORD_TOKEN=YOUR_TOKEN \
     -e GUILD_ID=YOUR_GUILD_ID \
     -e CHANNEL_ID=YOUR_CHANNEL_ID \
     -e STATUS=online \
     -e SELF_MUTE=true \
     -e SELF_DEAF=false \
     voicecord
   ```

5. Tail the logs to confirm it connected:

   ```bash
   docker logs -f voicecord
   ```

   To stop it: `docker stop voicecord`. To remove the container: `docker rm voicecord`.

---

## 🩺 Healthcheck

The container runs a tiny built-in HTTP endpoint that Docker uses to verify the bot is actually talking to Discord (not just that the process is alive).

- **Endpoint:** `GET /health` on `http://0.0.0.0:8080` inside the container (port configurable via `HEALTH_PORT`)
- **How it works:** every Discord gateway heartbeat updates a timestamp; the endpoint returns:
  - `200 OK` + `{"status":"ok", ...}` if a heartbeat was seen within `HEALTH_STALE_AFTER` seconds (default 60s)
  - `503 Service Unavailable` + `{"status":"stale", ...}` otherwise
- **Docker probe:** the `HEALTHCHECK` in the `Dockerfile` curls `/health` every 30s. After 3 failures the container is restarted automatically by Docker (combined with `--restart unless-stopped` this gives you self-healing 24/7 hosting).

Useful commands:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' voicecord

# Hit the health endpoint manually (from inside the container)
docker exec voicecord curl -s http://127.0.0.1:8080/health
```

You can tune the probe in the `Dockerfile` (`HEALTHCHECK` line) or the staleness threshold via `HEALTH_STALE_AFTER` in your `.env`.

---

<p align="center">Voicecord is licensed under <a href="https://github.com/SealedSaucer/Voicecord/blob/main/LICENSE">GNU General Public License</a> ❤️</p>
