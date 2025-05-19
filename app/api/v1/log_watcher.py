import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import re

XRAY_LOG_PATH = "/var/log/xray/access.log"  # <-- путь к логу Xray
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

class XrayLogTailer:
    def __init__(self):
        self.task = None
        self.running = False

    async def tail_log(self):
        print("🚀 tail_log запущен")
        self.running = True
        path = Path(XRAY_LOG_PATH)
        if not path.exists():
            print("❌ Log file doesn't exist:", XRAY_LOG_PATH)
            return

        # Пример строки Xray лога:
        # 2025/05/19 17:38:25 [info] proxy: accepted tcp:youtube.com:443 [UUID] --> ip:port

        log_pattern = re.compile(
            r'(?P<datetime>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?tcp:(?P<host>[^:]+):(?P<port>\d+)\s+\[(?P<uuid>[^\]]+)\].*?(\d{1,3}\.){3}\d{1,3}:(?P<client_port>\d+)'
        )

        async with aiohttp.ClientSession() as session:
            with open(XRAY_LOG_PATH, "r") as f:
                f.seek(0, 2)  # jump to end
                while self.running:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue

                    match = log_pattern.search(line)
                    if not match:
                        continue

                    try:
                        timestamp_str = match.group("datetime")
                        timestamp = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S").isoformat()
                        host = match.group("host")
                        port = int(match.group("port"))
                        uuid = match.group("uuid")

                        payload = {
                            "uuid": uuid,
                            "ip": None,  # Xray лог не всегда содержит исходный IP напрямую
                            "destination": f"{host}:{port}",
                            "raw_log": line.strip(),
                            "timestamp": timestamp,
                            "status": "CONNECTED",
                            "bytes_sent": None
                        }

                        print(f"📤 Отправляем: {payload}")
                        async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                            if resp.status != 201:
                                print(f"❗️Failed to send log: {resp.status}")
                    except Exception as e:
                        print(f"⚠️ Parse error: {e}")
                        continue

    async def start(self):
        if not self.task:
            self.task = asyncio.create_task(self.tail_log())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

tailer = XrayLogTailer()
