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
        self.server_ip = None


    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def find_squid_info(self, uuid, domain, xray_timestamp=None):
        if not os.path.exists(self.squid_log_path):
            return None, None
        try:
            async with aiofiles.open(self.squid_log_path, "r") as f:
                lines = deque(maxlen=1000)
                async for line in f:
                    lines.append(line)
            for line in reversed(lines):
                match = re.match(r"(\d+\.\d+) [^ ]+ [^ ]+ ([^ ]+) ([A-Z]+) ([^ ]+) (\d+) (\d+) ", line)
                if not match:
                    continue
                unix_ts, user, method, url, status, bytes_sent = match.groups()
                user_base = user.split("@")[0]
                url_domain = url.split(":")[0]
                # Сравниваем uuid и домен
                if uuid == user_base and domain == url_domain:
                    # Если есть время из Xray, сравниваем разницу
                    if xray_timestamp:
                        squid_time = float(unix_ts)
                        xray_time = xray_timestamp.timestamp()
                        if abs(squid_time - xray_time) > 10:  # 10 секунд окно
                            continue
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
                try:
                    dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                    timestamp_iso = dt.isoformat()
                    # Найдём статус и байты из squid (асинхронно, с учётом времени)
                    status, bytes_sent = await self.find_squid_info(uuid, domain, dt)

                    # Новая логика: если статус найден — accepted, иначе failed
                    if status is not None:
                        status_out = "accepted"
                    else:
                        status_out = "failed"

                    payload = {
                        "uuid": uuid,
                        "ip": ip,
                        "destination": domain,
                        "timestamp": timestamp_iso,
                        "status": status_out,
                        "bytes_sent": bytes_sent,
                        "server_ip": self.server_ip
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
        if not hasattr(self, "server_ip"):
            self.server_ip = None

        if not self.server_ip:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.ipify.org") as resp:
                        self.server_ip = await resp.text()
                        print(f"🌍 Внешний IP сервера: {self.server_ip}")
            except Exception as e:
                print(f"❌ Не удалось получить IP: {e}")
                self.server_ip = "unknown"

        if not self.task:
            self.task = asyncio.create_task(self.tail_log())

tailer = XrayLogTailer()