import asyncio
import aiohttp
import re
from datetime import datetime
from asyncio.subprocess import PIPE, create_subprocess_exec
import os
import aiofiles
from collections import deque

# SQUID_LOG_PATH = "/logs/squid/access.log"

XRAY_LOG_PATH = "/logs/xray/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

class XrayLogTailer:
    def __init__(self):
        self.task = None
        self.running = False
        self.squid_log_path = "/logs/squid/access.log"

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def find_squid_info(self, uuid, domain):
        """
        Асинхронно ищет последнюю подходящую строку в логе Squid по uuid/email и домену,
        возвращает (status, bytes_sent) или (None, None) если не найдено.
        """
        if not os.path.exists(self.squid_log_path):
            return None, None
        try:
            # Читаем только последние 1000 строк для ускорения
            async with aiofiles.open(self.squid_log_path, "r") as f:
                lines = deque(maxlen=1000)
                async for line in f:
                    lines.append(line)
            for line in reversed(lines):
                # logformat compact: ... <user> <method> <url> <status> <bytes_sent> ...
                match = re.match(r"\d+\.\d+ [^ ]+ [^ ]+ ([^ ]+) ([A-Z]+) ([^ ]+) (\d+) (\d+) ", line)
                if not match:
                    continue
                user, method, url, status, bytes_sent = match.groups()
                # user = uuid, url = domain:port
                if uuid == user and domain in url:
                    return status, int(bytes_sent)
        except Exception as e:
            print(f"Ошибка поиска в squid access.log: {e}")
        return None, None

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
                # Найдём статус и байты из squid (асинхронно)
                status, bytes_sent = await self.find_squid_info(uuid, domain)
                try:
                    dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                    timestamp_iso = dt.isoformat()

                    payload = {
                        "uuid": uuid,
                        "ip": ip,
                        "destination": domain,
                        "timestamp": timestamp_iso,
                        "status": status,
                        "bytes_sent": bytes_sent
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