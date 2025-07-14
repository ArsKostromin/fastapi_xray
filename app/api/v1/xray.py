from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from uuid import UUID
import json
import aiofiles
import asyncio
import subprocess
import logging
from fastapi.responses import JSONResponse

router = APIRouter()

# Пути
XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")
SQUID_PASSWD_FILE = Path("/etc/squid/passwd")
SQUID_DEFAULT_PASSWORD = "x"
XRAY_CONTAINER_NAME = "xray"

# Настройка логов
logger = logging.getLogger("vless")
logging.basicConfig(level=logging.INFO)


class VLESSRequest(BaseModel):
    uuid: str


class VLESSResponse(BaseModel):
    success: bool
    vless_link: str = ""
    message: str = ""


async def add_user_to_htpasswd(user: str, password: str):
    """Добавляет или обновляет пользователя в htpasswd"""
    try:
        logger.info(f"Добавление пользователя {user} в htpasswd")
        result = subprocess.run(
            ["htpasswd", "-b", "-m", SQUID_PASSWD_FILE, user, password],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Пользователь {user} успешно добавлен")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка htpasswd: {e.stderr.decode().strip()}")
        raise RuntimeError(f"htpasswd error: {e.stderr.decode().strip()}")


async def restart_xray():
    """Перезапуск контейнера Xray через docker"""
    try:
        logger.info(f"Перезапуск контейнера {XRAY_CONTAINER_NAME}")
        proc = await asyncio.create_subprocess_exec(
            "docker", "restart", XRAY_CONTAINER_NAME,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode().strip())
        logger.info(f"Контейнер {XRAY_CONTAINER_NAME} перезапущен")
    except Exception as e:
        logger.error(f"Ошибка перезапуска Xray: {e}")
        raise


@router.post("/vless", response_model=VLESSResponse)
async def create_vless_user(data: VLESSRequest):
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        logger.info(f"Открытие Xray-конфига: {XRAY_CONFIG_PATH}")
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        clients = config["inbounds"][0]["settings"]["clients"]
        outbounds = config.get("outbounds", [])
        routing_rules = config.get("routing", {}).get("rules", [])

        if any(client["id"] == uid for client in clients):
            logger.warning(f"UUID уже существует: {uid}")
            return VLESSResponse(success=False, message="UUID already exists")

        # Добавляем клиента
        email = f"{uid}@vpn"
        clients.append({
            "id": uid,
            "level": 0,
            "email": email
        })
        logger.info(f"Клиент {uid} добавлен")

        # Добавляем outbound (если ещё не существует)
        outbound_tag = f"user-{uid}"
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

        if any(o.get("tag") == outbound_tag for o in outbounds):
            logger.warning(f"Outbound с тегом {outbound_tag} уже существует")
        else:
            outbounds.append(new_outbound)
            logger.info(f"Outbound {outbound_tag} добавлен")

        config["outbounds"] = outbounds

        # Добавляем routing rule (если ещё не существует)
        if "routing" not in config:
            config["routing"] = {"domainStrategy": "AsIs", "rules": []}

        if not any(rule.get("email") == email for rule in config["routing"]["rules"]):
            config["routing"]["rules"].append({
                "type": "field",
                "inboundTag": ["vless-single"],
                "email": email,
                "outboundTag": outbound_tag
            })
            logger.info(f"Правило маршрутизации для {email} добавлено")
        else:
            logger.warning(f"Routing правило для {email} уже существует")

        # Сохраняем конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))
        logger.info("Конфиг успешно записан")

        # Обновляем htpasswd
        await add_user_to_htpasswd(uid, SQUID_DEFAULT_PASSWORD)

        # Перезапускаем Xray
        await restart_xray()

        # Ссылка
        domain = "indonesia.server2.anonixvpn.space"
        port = 443
        path = "/vless"

        vless_link = (
            f"vless://{uid}@{domain}:{port}"
            f"?encryption=none&security=tls&type=ws&host=indonesia.server2.anonixvpn.space&path=%2Fws#indonesia"
        )

        logger.info(f"VLESS ссылка сгенерирована: {vless_link}")
        return VLESSResponse(success=True, vless_link=vless_link, message="VLESS user created")

    except Exception as e:
        logger.error(f"Ошибка при создании VLESS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vless", response_model=VLESSResponse)
async def delete_vless_user(data: VLESSRequest):
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        logger.info(f"Удаление VLESS-пользователя {uid}")
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        clients = config["inbounds"][0]["settings"]["clients"]
        original_len = len(clients)
        clients = [client for client in clients if client["id"] != uid]

        if len(clients) == original_len:
            logger.warning(f"UUID {uid} не найден")
            return VLESSResponse(success=False, message="UUID not found")

        config["inbounds"][0]["settings"]["clients"] = clients
        config["outbounds"] = [
            o for o in config.get("outbounds", [])
            if not any(u.get("user") == uid for s in o.get("settings", {}).get("servers", []) for u in s.get("users", []))
        ]
        config["routing"]["rules"] = [
            r for r in config["routing"]["rules"] if r.get("email") != f"{uid}@vpn"
        ]

        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))
        logger.info("Конфиг обновлён после удаления пользователя")

        await restart_xray()
        return VLESSResponse(success=True, message="VLESS user deleted")

    except Exception as e:
        logger.error(f"Ошибка при удалении VLESS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


#получение колличества пользователей
@router.get("/vless/count")
async def count_vless_users():
    try:
        logger.info(f"Подсчёт пользователей в конфиге: {XRAY_CONFIG_PATH}")
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        clients = config["inbounds"][0]["settings"].get("clients", [])
        user_count = len(clients)
        logger.info(f"Найдено пользователей: {user_count}")
        return JSONResponse(content={"user_count": user_count})
    except Exception as e:
        logger.error(f"Ошибка при подсчёте VLESS-пользователей: {e}")
        raise HTTPException(status_code=500, detail=str(e))
