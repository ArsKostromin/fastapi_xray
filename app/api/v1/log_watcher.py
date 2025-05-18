# log_watcher.py
import asyncio
import aiohttp
import socket
from pathlib import Path
from datetime import datetime

LOG_PATH = "/var/log/squid/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

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

        async with aiohttp.ClientSession() as session:
            with open(LOG_PATH, "r") as f:
                f.seek(0, 2)  # jump to end
                while self.running:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue

                    parts = line.strip().split()
                    if len(parts) < 5:
                        continue

                    # Парсим поля
                    try:
                        timestamp_unix = float(parts[0])
                        timestamp = datetime.utcfromtimestamp(timestamp_unix).isoformat()
                        client_ip = parts[2]
                        status_code = parts[3].split("/")[1] if "/" in parts[3] else None
                        bytes_sent = int(parts[4])
                        destination = parts[6] if len(parts) > 6 else None
                        email = parts[7] if len(parts) > 7 and "@" in parts[7] else None
                    except Exception as e:
                        print(f"Parse error: {e}")
                        continue

                    payload = {
                        "uuid": email or "unknown",
                        "ip": client_ip,
                        "destination": destination,
                        "raw_log": line.strip(),
                        "timestamp": timestamp,
                        "status": status_code,
                        "bytes_sent": bytes_sent,
                    }

                    try:
                        async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                            if resp.status != 201:
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

tailer = LogTailer()
