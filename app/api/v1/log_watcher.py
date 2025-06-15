import asyncio
import aiohttp
import re
from datetime import datetime
from subprocess import PIPE, create_subprocess_exec

# SQUID_LOG_PATH = "/logs/squid/access.log"

XRAY_LOG_PATH = "/logs/xray/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

class XrayLogTailer:
    def __init__(self):
        self.task = None
        self.running = False

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def parse_xray_log(self):
        print("📦 Запущен парсер Xray access.log через cat + tail -F")

        try:
            proc = await create_subprocess_exec(
                "tail", "-F", XRAY_LOG_PATH,
                stdout=PIPE, stderr=PIPE
            )
        except FileNotFoundError:
            print(f"❌ Не удалось найти файл {XRAY_LOG_PATH}")
            return

        async with aiohttp.ClientSession() as session:
            while self.running:
                line = await proc.stdout.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                line = line.decode().strip()
                match = re.search(
                    r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\.\d+ from ([\d\.]+):\d+ accepted tcp:([^:]+):\d+ .*email: ([a-f0-9\-]+)",
                    line
                )
                if not match:
                    continue

                timestamp_str, ip, domain, uuid = match.groups()
                try:
                    dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                    timestamp_iso = dt.isoformat()

                    payload = {
                        "uuid": uuid,
                        "ip": ip,
                        "destination": domain,
                        "timestamp": timestamp_iso,
                    }

                    print(f"📤 Отправляем лог: {payload}")
                    async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                        if resp.status != 201:
                            print(f"❗️Ошибка отправки: {resp.status}")
                except Exception as e:
                    print(f"⚠️ Ошибка обработки строки: {e}")

    async def tail_log(self):
        self.running = True
        await self.parse_xray_log()

    async def start(self):
        if not self.task:
            self.task = asyncio.create_task(self.tail_log())

tailer = XrayLogTailer()
