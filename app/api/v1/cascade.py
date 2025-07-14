from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from uuid import UUID, uuid4
import json
import aiofiles
import asyncio
import subprocess
import logging
from fastapi.responses import JSONResponse

router = APIRouter()

# Пути
XRAY_CONFIG_PATH = Path("/usr/local/etc/xray/config.json")
XRAY_CONTAINER_NAME = "xray"

# Настройка логов
logger = logging.getLogger("cascade")
logging.basicConfig(level=logging.INFO)


class CascadeRequest(BaseModel):
    uuid: str
    server2_ip: str
    server2_port: int = 8443


class CascadeResponse(BaseModel):
    success: bool
    vless_link: str = ""
    message: str = ""
    cascade_uuid: str = ""


class CascadeConfig(BaseModel):
    server2_ip: str
    server2_port: int = 8443
    server2_uuid: str = ""


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


@router.post("/cascade", response_model=CascadeResponse)
async def create_cascade_user(data: CascadeRequest):
    """Создает пользователя для каскадного соединения (двойное шифрование)"""
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        logger.info(f"Создание каскадного пользователя {uid}")
        
        # Генерируем UUID для второго сервера
        server2_uuid = str(uuid4())
        
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        # Проверяем, есть ли уже каскадный inbound
        cascade_inbound = None
        for inbound in config.get("inbounds", []):
            if inbound.get("tag") == "vless-cascade":
                cascade_inbound = inbound
                break

        if not cascade_inbound:
            # Создаем каскадный inbound
            cascade_inbound = {
                "port": 1443,
                "protocol": "vless",
                "settings": {
                    "clients": [],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "tls",
                    "tlsSettings": {
                        "certificates": [
                            {
                                "certificateFile": "/etc/letsencrypt/live/germany.anonixvpn.space/fullchain.pem",
                                "keyFile": "/etc/letsencrypt/live/germany.anonixvpn.space/privkey.pem"
                            }
                        ]
                    },
                    "wsSettings": {
                        "path": "/cascade",
                        "headers": {
                            "Host": "germany.anonixvpn.space"
                        }
                    }
                },
                "tag": "vless-cascade",
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"]
                }
            }
            config["inbounds"].append(cascade_inbound)
            logger.info("Каскадный inbound создан")

        # Добавляем клиента в каскадный inbound
        clients = cascade_inbound["settings"]["clients"]
        if any(client["id"] == uid for client in clients):
            logger.warning(f"UUID уже существует в каскаде: {uid}")
            return CascadeResponse(success=False, message="UUID already exists in cascade")

        email = f"{uid}@cascade"
        clients.append({
            "id": uid,
            "level": 0,
            "email": email
        })
        logger.info(f"Клиент {uid} добавлен в каскад")

        # Проверяем/создаем outbound для каскада
        cascade_outbound = None
        for outbound in config.get("outbounds", []):
            if outbound.get("tag") == "cascade-to-server2":
                cascade_outbound = outbound
                break

        if not cascade_outbound:
            cascade_outbound = {
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": data.server2_ip,
                            "port": data.server2_port,
                            "users": [
                                {
                                    "id": server2_uuid,
                                    "level": 0,
                                    "encryption": "none"
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "none"
                },
                "tag": "cascade-to-server2"
            }
            config["outbounds"].append(cascade_outbound)
            logger.info("Каскадный outbound создан")
        else:
            # Обновляем настройки второго сервера
            cascade_outbound["settings"]["vnext"][0]["address"] = data.server2_ip
            cascade_outbound["settings"]["vnext"][0]["port"] = data.server2_port
            cascade_outbound["settings"]["vnext"][0]["users"][0]["id"] = server2_uuid

        # Проверяем/создаем routing rules
        if "routing" not in config:
            config["routing"] = {"domainStrategy": "IPIfNonMatch", "rules": []}

        # Добавляем правило для каскада
        cascade_rule = {
            "type": "field",
            "inboundTag": ["vless-cascade"],
            "outboundTag": "cascade-to-server2"
        }

        if not any(rule.get("inboundTag") == ["vless-cascade"] for rule in config["routing"]["rules"]):
            config["routing"]["rules"].append(cascade_rule)
            logger.info("Правило маршрутизации для каскада добавлено")

        # Сохраняем конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))
        logger.info("Конфиг успешно записан")

        # Перезапускаем Xray
        await restart_xray()

        # Генерируем ссылку для каскада
        domain = "germany.anonixvpn.space"
        port = 1443
        path = "/cascade"

        vless_link = (
            f"vless://{uid}@{domain}:{port}"
            f"?encryption=none&security=tls&type=ws&host={domain}&path=%2Fcascade#cascade-double-encryption"
        )

        logger.info(f"Каскадная VLESS ссылка сгенерирована: {vless_link}")
        
        return CascadeResponse(
            success=True, 
            vless_link=vless_link, 
            message="Cascade user created successfully",
            cascade_uuid=server2_uuid
        )

    except Exception as e:
        logger.error(f"Ошибка при создании каскадного пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cascade", response_model=CascadeResponse)
async def delete_cascade_user(data: CascadeRequest):
    """Удаляет пользователя из каскадного соединения"""
    try:
        uid = str(UUID(data.uuid))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    try:
        logger.info(f"Удаление каскадного пользователя {uid}")
        
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        # Ищем каскадный inbound
        cascade_inbound = None
        for inbound in config.get("inbounds", []):
            if inbound.get("tag") == "vless-cascade":
                cascade_inbound = inbound
                break

        if not cascade_inbound:
            logger.warning("Каскадный inbound не найден")
            return CascadeResponse(success=False, message="Cascade inbound not found")

        # Удаляем клиента из каскадного inbound
        clients = cascade_inbound["settings"]["clients"]
        original_len = len(clients)
        clients = [client for client in clients if client["id"] != uid]

        if len(clients) == original_len:
            logger.warning(f"UUID {uid} не найден в каскаде")
            return CascadeResponse(success=False, message="UUID not found in cascade")

        cascade_inbound["settings"]["clients"] = clients
        logger.info(f"Клиент {uid} удален из каскада")

        # Если каскадный inbound пустой, удаляем его
        if not clients:
            config["inbounds"] = [inbound for inbound in config["inbounds"] if inbound.get("tag") != "vless-cascade"]
            logger.info("Пустой каскадный inbound удален")

        # Удаляем правило маршрутизации для каскада, если inbound удален
        if not clients:
            config["routing"]["rules"] = [
                rule for rule in config["routing"]["rules"] 
                if rule.get("inboundTag") != ["vless-cascade"]
            ]
            logger.info("Правило маршрутизации для каскада удалено")

        # Сохраняем конфиг
        async with aiofiles.open(XRAY_CONFIG_PATH, "w") as f:
            await f.write(json.dumps(config, indent=2))
        logger.info("Конфиг успешно обновлен")

        # Перезапускаем Xray
        await restart_xray()

        return CascadeResponse(success=True, message="Cascade user deleted successfully")

    except Exception as e:
        logger.error(f"Ошибка при удалении каскадного пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cascade/count")
async def count_cascade_users():
    """Возвращает количество пользователей в каскаде"""
    try:
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        cascade_inbound = None
        for inbound in config.get("inbounds", []):
            if inbound.get("tag") == "vless-cascade":
                cascade_inbound = inbound
                break

        if not cascade_inbound:
            return {"count": 0}

        count = len(cascade_inbound["settings"]["clients"])
        return {"count": count}

    except Exception as e:
        logger.error(f"Ошибка при подсчете каскадных пользователей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cascade/list")
async def list_cascade_users():
    """Возвращает список пользователей в каскаде"""
    try:
        async with aiofiles.open(XRAY_CONFIG_PATH, "r") as f:
            config_data = await f.read()
        config = json.loads(config_data)

        cascade_inbound = None
        for inbound in config.get("inbounds", []):
            if inbound.get("tag") == "vless-cascade":
                cascade_inbound = inbound
                break

        if not cascade_inbound:
            return {"users": []}

        users = [client["id"] for client in cascade_inbound["settings"]["clients"]]
        return {"users": users}

    except Exception as e:
        logger.error(f"Ошибка при получении списка каскадных пользователей: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 