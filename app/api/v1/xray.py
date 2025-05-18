from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from uuid import UUID
import json
import aiofiles
import asyncio

router = APIRouter()

XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")


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

        # Добавляем нового клиента
        clients.append({
            "id": uid,
            "level": 0,
            "email": f"{uid}@vpn"
        })

        # Сохраняем конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))

        # Генерация ссылки
        domain = "159.198.77.150"
        port = 80
        path = "/vless"

        vless_link = (
            f"vless://{uid}@{domain}:{port}"
            f"?encryption=none&type=ws&security=none&path={path}#AnonVPN"
        )

        # Перезапуск Xray
        await asyncio.create_subprocess_exec("supervisorctl", "restart", "xray")

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

        # Фильтруем клиентов
        clients = [client for client in clients if client["id"] != uid]

        if len(clients) == original_len:
            return VLESSResponse(success=False, message="UUID not found")

        config["inbounds"][0]["settings"]["clients"] = clients

        # Перезаписываем конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))

        await asyncio.create_subprocess_exec("supervisorctl", "restart", "xray")

        return VLESSResponse(success=True, message="VLESS user deleted")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
