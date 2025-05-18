import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

LOG_PATH = "/var/log/squid/access.log"
CENTRAL_LOG_SERVER = "https://your-central-logger.com/receive"

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

                    payload = {
                        "ip": "squid-box",  # или socket.gethostname()
                        "timestamp": datetime.utcnow().isoformat(),
                        "log": line.strip()
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
