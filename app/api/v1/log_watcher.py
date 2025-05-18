import asyncio
import aiohttp
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
                    if len(parts) < 6:
                        continue

                    try:
                        timestamp_unix = float(parts[0])
                        timestamp = datetime.utcfromtimestamp(timestamp_unix).isoformat()
                        client_ip = parts[1]
                        uuid = parts[2]
                        method = parts[3]
                        host_port = parts[4]

                        # Разделяем host:port
                        if ':' in host_port:
                            host, port_str = host_port.split(":", 1)
                            port = int(port_str)
                        else:
                            host = host_port
                            port = None

                        status_code = parts[5]

                        payload = {
                            "uuid": uuid,
                            "ip": client_ip,
                            "destination": f"{host}:{port}" if port else host,
                            "raw_log": line.strip(),
                            "timestamp": timestamp,
                            "status": status_code,
                            "bytes_sent": None  # нет в твоем формате
                        }

                        async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                            if resp.status != 201:
                                print(f"Failed to send log: {resp.status}")
                    except Exception as e:
                        print(f"Parse error: {e}")
                        continue

    def start(self):
        if not self.task:
            self.task = asyncio.create_task(self.tail_log())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

tailer = LogTailer()
