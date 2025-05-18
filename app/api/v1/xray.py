from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from uuid import UUID
import json
import aiofiles
import asyncio
import subprocess

router = APIRouter()

XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")
SQUID_PASSWD_FILE = Path("/etc/squid/passwd")
SQUID_DEFAULT_PASSWORD = "x"


class VLESSRequest(BaseModel):
    uuid: str


class VLESSResponse(BaseModel):
    success: bool
    vless_link: str = ""
    message: str = ""


async def add_user_to_htpasswd(user: str, password: str):
    """Добавляет или обновляет пользователя в htpasswd"""
    try:
        result = subprocess.run(
            ["htpasswd", "-bB", SQUID_PASSWD_FILE, user, password],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"htpasswd error: {e.stderr.decode().strip()}")


@router.post("/vless", response_model=VLESSResponse)
async def create_vless_user(data: VLESSRequest):
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        # Загружаем текущий конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()

        config = json.loads(config_data)

        clients = config["inbounds"][0]["settings"]["clients"]
        outbounds = config.get("outbounds", [])
        routing_rules = config.get("routing", {}).get("rules", [])

        if any(client["id"] == uid for client in clients):
            return VLESSResponse(success=False, message="UUID already exists")

        # Добавляем клиента
        email = f"{uid}@vpn"
        clients.append({
            "id": uid,
            "level": 0,
            "email": email
        })

        # Добавляем outbound
        outbound_tag = f"user-{uid[:6]}"
        new_outbound = {
            "protocol": "http",
            "settings": {
                "servers": [
                    {
                        "address": "127.0.0.1",
                        "port": 8888,
                        "users": [
                            {
                                "user": uid,
                                "pass": SQUID_DEFAULT_PASSWORD,
                                "auth": "basic"
                            }
                        ]
                    }
                ]
            },
            "tag": outbound_tag
        }
        outbounds.append(new_outbound)

        # Добавляем routing rule
        new_rule = {
            "type": "field",
            "inboundTag": ["vless-in"],
            "email": email,
            "outboundTag": outbound_tag
        }
        routing_rules.append(new_rule)

        # Сохраняем обновлённый конфиг
        config["outbounds"] = outbounds
        if "routing" not in config:
            config["routing"] = {"domainStrategy": "AsIs", "rules": []}
        config["routing"]["rules"] = routing_rules

        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))

        # Обновляем htpasswd
        await add_user_to_htpasswd(uid, SQUID_DEFAULT_PASSWORD)

        # Перезапускаем Xray
        await asyncio.create_subprocess_exec("sudo", "systemctl", "restart", "xray")

        # Генерируем ссылку
        domain = "159.198.77.150"
        port = 80
        path = "/vless"

        vless_link = (
            f"vless://{uid}@{domain}:{port}"
            f"?encryption=none&type=ws&security=none&path={path}#AnonVPN"
        )

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

        await asyncio.create_subprocess_exec("sudo", "systemctl", "restart", "xray")

        return VLESSResponse(success=True, message="VLESS user deleted")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
