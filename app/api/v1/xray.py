from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from uuid import UUID
import json
import socket
import aiofiles
import aiohttp
import asyncio

router = APIRouter()

XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")
CENTRAL_LOG_SERVER = "http://example.com/api/logs"


class VLESSRequest(BaseModel):
    uuid: str


class VLESSResponse(BaseModel):
    success: bool
    vless_link: str = ""
    message: str = ""


@router.post("/vless", response_model=VLESSResponse)
async def create_vless_user(data: VLESSRequest):
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)
        clients = config["inbounds"][0]["settings"]["clients"]

        if any(client["id"] == uid for client in clients):
            return VLESSResponse(success=False, message="UUID already exists")

        clients.append({
            "id": uid,
            "flow": "xtls-rprx-vision"
        })

        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))

        short_id = config["inbounds"][0]["streamSettings"]["realitySettings"]["shortIds"][0]
        public_key = config["inbounds"][0]["streamSettings"]["realitySettings"]["publicKey"]
        domain = "159.198.77.150"
        sni = "www.cloudflare.com"

        vless_link = (
            f"vless://{uid}@{domain}:443"
            f"?encryption=none&flow=xtls-rprx-vision&security=reality"
            f"&sni={sni}&fp=chrome&pbk={public_key}&sid={short_id}"
            f"&type=tcp&headerType=none#Reality-VLESS"
        )

        # Асинхронно перезапускаем xray
        await asyncio.create_subprocess_exec("sudo", "systemctl", "restart", "xray")

        return VLESSResponse(success=True, vless_link=vless_link, message="VLESS user created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vless", response_model=VLESSResponse)
async def delete_vless_user(data: VLESSRequest):
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)
        clients = config["inbounds"][0]["settings"]["clients"]
        original_len = len(clients)

        clients = [client for client in clients if client["id"] != uid]

        if len(clients) == original_len:
            return VLESSResponse(success=False, message="UUID not found")

        config["inbounds"][0]["settings"]["clients"] = clients
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))

        await asyncio.create_subprocess_exec("sudo", "systemctl", "restart", "xray")

        return VLESSResponse(success=True, message="VLESS user deleted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-logs")
async def send_logs():
    try:
        log_path = Path("/var/log/xray/access.log")
        if not log_path.exists():
            return {"status": "no logs"}

        async with aiofiles.open(log_path, "r") as f:
            lines = await f.readlines()
        logs = lines[-100:]

        ip = socket.gethostbyname(socket.gethostname())
        payload = {
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat(),
            "logs": logs,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(CENTRAL_LOG_SERVER, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to send logs, status: {resp.status}")
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}
