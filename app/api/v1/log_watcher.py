import asyncio
import aiohttp
import re
from datetime import datetime
from pathlib import Path

SQUID_LOG_PATH = "/var/log/squid/access.log"
XRAY_LOG_PATH = "/var/log/xray/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

class XraySquidLogTailer:
    def __init__(self):
        self.task = None
        self.running = False
        self.xray_entries = []  # Список словарей с time+uuid из xray

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def parse_xray_log(self):
        """
        Парсит Xray access.log и сохраняет UUID и timestamp (unix) в список
        """
        print("📦 Запущен парсер Xray access.log")
        path = Path(XRAY_LOG_PATH)
        if not path.exists():
            print("❌ Xray лог не найден:", XRAY_LOG_PATH)
            return

        with open(XRAY_LOG_PATH, "r") as f:
            f.seek(0, 2)  # Конец файла
            while self.running:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue

                match = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*email: ([a-f0-9\-]+)", line)
                if match:
                    timestamp_str = match.group(1)
                    uuid = match.group(2)
                    try:
                        dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                        timestamp_unix = dt.timestamp()
                        self.xray_entries.append({
                            "timestamp": timestamp_unix,
                            "uuid": uuid
                        })
                        if len(self.xray_entries) > 1000:
                            self.xray_entries = self.xray_entries[-1000:]  # Очистка старых
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки Xray лога: {e}")

    def find_uuid_by_timestamp(self, squid_ts):
        # Находит ближайший по времени UUID
        closest = None
        min_diff = float('inf')
        for entry in self.xray_entries:
            diff = abs(entry['timestamp'] - squid_ts)
            if diff < min_diff:
                min_diff = diff
                closest = entry
        return closest['uuid'] if closest else None

    async def tail_squid_log(self):
        print("🚀 Запущен парсер Squid access.log")
        path = Path(SQUID_LOG_PATH)
        if not path.exists():
            print("❌ Squid лог не найден:", SQUID_LOG_PATH)
            return

        async with aiohttp.ClientSession() as session:
            with open(SQUID_LOG_PATH, "r") as f:
                f.seek(0, 2)
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
                        method = parts[3]
                        host_port = parts[4]
                        status_code = parts[5]

                        if ':' in host_port:
                            host, port_str = host_port.split(":", 1)
                            port = int(port_str)
                        else:
                            host = host_port
                            port = None

                        # ищем UUID по таймстемпу
                        uuid = self.find_uuid_by_timestamp(timestamp_unix)
                        if not uuid:
                            print("⚠️ UUID не найден по таймстемпу", timestamp_unix)
                            continue

                        payload = {
                            "uuid": uuid,
                            "ip": client_ip,
                            "destination": f"{host}:{port}" if port else host,
                            "raw_log": line.strip(),
                            "timestamp": timestamp,
                            "status": status_code,
                            "bytes_sent": None
                        }

                        print(f"📤 Отправляем лог: {payload}")
                        async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                            if resp.status != 201:
                                print(f"❗️Ошибка отправки: {resp.status}")
                    except Exception as e:
                        print(f"⚠️ Ошибка парсинга: {e}")

    async def tail_log(self):
        self.running = True
        await asyncio.gather(
            self.parse_xray_log(),
            self.tail_squid_log()
        )

    async def start(self):
        if not self.task:
            self.task = asyncio.create_task(self.tail_log())
            
tailer = XraySquidLogTailer()
