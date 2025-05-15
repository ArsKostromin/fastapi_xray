from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import json
from pathlib import Path
from datetime import datetime
import socket
import requests

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
def create_vless_user(data: VLESSRequest):
    try:
        uid = str(uuid.UUID(data.uuid))  # validate UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        config = json.loads(XRAY_CONFIG_PATH.read_text())
        clients = config["inbounds"][0]["settings"]["clients"]

        if any(client["id"] == uid for client in clients):
            return VLESSResponse(success=False, message="UUID already exists")

        clients.append({
            "id": uid,
            "flow": "xtls-rprx-vision"
        })

        XRAY_CONFIG_PATH.write_text(json.dumps(config, indent=2))

        short_id = config["inbounds"][0]["streamSettings"]["realitySettings"]["shortIds"][0]
        server_name = config["inbounds"][0]["streamSettings"]["realitySettings"]["serverNames"][0]
        domain = server_name
        vless_link = f"vless://{uid}@{domain}:443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk={config['inbounds'][0]['streamSettings']['realitySettings']['privateKey']}&sid={short_id}&sni={server_name}#{uid}"

        return VLESSResponse(success=True, vless_link=vless_link, message="VLESS user created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def send_logs():
    try:
        log_path = Path("/var/log/xray/access.log")  # заменить, если другой путь
        if not log_path.exists():
            return

        with log_path.open() as f:
            logs = f.readlines()[-100:]  # последние 100 строк

        ip = socket.gethostbyname(socket.gethostname())
        payload = {
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat(),
            "logs": logs,
        }

        response = requests.post(CENTRAL_LOG_SERVER, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send logs: {e}")
