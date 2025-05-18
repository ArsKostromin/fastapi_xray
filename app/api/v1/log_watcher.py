# log_watcher.py
import asyncio
import aiohttp
import socket
from pathlib import Path
from datetime import datetime

LOG_PATH = "/var/log/squid/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/api/v1/proxylog/"  # Django endpoint

class LogTailer:
    def __init__(self):
        self.task = None
        self.running = False

    async def tail_log(self):
        self.running = True
        path = Path(LOG_PATH)
        if not path.exists():
            print("Log file doesn't exist:", LOG_PATH)
            return

        hostname = socket.gethostname()

        async with aiohttp.ClientSession() as session:
            with open(LOG_PATH, "r") as f:
                f.seek(0, 2)  # jump to end
                while self.running:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue

                    # Пример строки: 1747585954.066  59099 81.162.252.10 NONE/503 0 CONNECT 141.8.199.52:7070 - HIER_NONE/- -
                    parts = line.strip().split()
                    if len(parts) < 7:
                        continue

                    client_ip = parts[2]
                    destination = parts[6]
                    email = parts[7] if len(parts) > 7 and "@" in parts[7] else None

                    payload = {
                        "uuid": email or "unknown",
                        "ip": client_ip,
                        "host": hostname,
                        "destination": destination,
                        "raw_log": line.strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    try:
                        async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                            if resp.status != 200:
                                print(f"Failed to send log: {resp.status}")
                    except Exception as e:
                        print(f"Error sending log: {e}")

    def start(self):
        if not self.task:
            self.task = asyncio.create_task(self.tail_log())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

# Важно: создаём один tailer на весь проект
tailer = LogTailer()
