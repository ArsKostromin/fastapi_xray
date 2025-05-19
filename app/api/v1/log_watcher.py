import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta

SQUID_LOG_PATH = "/var/log/squid/access.log"
XRAY_LOG_PATH = "/var/log/xray/access.log"
CENTRAL_LOG_SERVER = "https://server2.anonixvpn.space/proxylogs/receive-log/"

xray_cache = {}

class LogTailer:
    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        if not self.task:
            self.running = True
            self.task = asyncio.create_task(self.tail_logs())
            print("🚀 LogTailer запущен")

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
            print("🛑 LogTailer остановлен")

    async def tail_logs(self):
        print("📄 tail_logs запущен")
        squid_path = Path(SQUID_LOG_PATH)
        xray_path = Path(XRAY_LOG_PATH)

        if not squid_path.exists() or not xray_path.exists():
            print("❌ Логи не найдены.")
            return

        squid_file = open(squid_path, "r")
        xray_file = open(xray_path, "r")

        squid_file.seek(0, 2)
        xray_file.seek(0, 2)

        async with aiohttp.ClientSession() as session:
            while self.running:
                squid_line = squid_file.readline()
                xray_line = xray_file.readline()

                if xray_line:
                    self._parse_xray_line(xray_line)

                if squid_line:
                    squid_event = self._parse_squid_line(squid_line)
                    if squid_event:
                        matched_email = self._match_squid_with_xray(squid_event)
                        if matched_email:
                            squid_event["email"] = matched_email
                            await self._send_to_server(session, squid_event)
                        else:
                            print(f"⚠️ Не найдено соответствие: {squid_event}")
                else:
                    await asyncio.sleep(0.3)

    def _parse_xray_line(self, line: str):
        if "accepted" not in line:
            return
        try:
            parts = line.strip().split()
            timestamp_str = " ".join(parts[0:2])
            timestamp = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S.%f")

            ip_port = parts[3]
            ip = ip_port.split(":")[0]

            email = None
            for part in parts:
                if part.startswith("email:"):
                    email = part.split("email:")[1]
                    break

            if not email:
                return

            xray_cache[ip] = {
                "email": email,
                "timestamp": timestamp
            }

        except Exception as e:
            print(f"❌ Ошибка XRAY: {e}")

    def _parse_squid_line(self, line: str):
        try:
            parts = line.strip().split()
            if len(parts) < 6:
                return None

            timestamp_unix = float(parts[0])
            timestamp = datetime.utcfromtimestamp(timestamp_unix)
            client_ip = parts[1]
            uuid = parts[2]
            method = parts[3]
            host_port = parts[4]
            status_code = parts[5]

            host, port = None, None
            if ":" in host_port:
                host, port_str = host_port.split(":", 1)
                port = int(port_str)

            return {
                "timestamp": timestamp,
                "client_ip": client_ip,
                "uuid": uuid,
                "method": method,
                "host": host,
                "port": port,
                "status": status_code,
            }
        except Exception as e:
            print(f"❌ Ошибка Squid: {e}")
            return None

    def _match_squid_with_xray(self, squid_event):
        ip = squid_event["client_ip"]
        squid_time = squid_event["timestamp"]

        if ip in xray_cache:
            xray_event = xray_cache[ip]
            xray_time = xray_event["timestamp"]
            delta = abs((squid_time - xray_time).total_seconds())
            if delta <= 2:
                return xray_event["email"]

        return None

    async def _send_to_server(self, session, data):
        try:
            payload = {
                "timestamp": data["timestamp"].isoformat(),
                "uuid": data["uuid"],
                "email": data.get("email"),
                "ip": data["client_ip"],
                "method": data["method"],
                "host": data["host"],
                "port": data["port"],
                "status": data["status"],
            }

            async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                if resp.status == 200:
                    print(f"✅ Лог отправлен: {payload}")
                else:
                    print(f"❌ Ошибка отправки: {resp.status}")
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
