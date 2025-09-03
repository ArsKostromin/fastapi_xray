# 🐳 Docker Compose Management

## 📋 Обзор

Ansible автоматически управляет Docker Compose для развертывания FastAPI и Xray сервисов. Все контейнеры запускаются через `docker-compose up --build`.

## 🔧 Что развертывается

### 1. **Xray Container**
- **Образ**: `teddysun/xray`
- **Порт**: 443 (host network)
- **Конфигурация**: `./xray/config.json`
- **Логи**: `./logs/xray/`

### 2. **FastAPI Container**
- **Сборка**: Из локального Dockerfile
- **Порт**: 8081
- **Зависимости**: Python 3.13, Docker CLI, Apache2-utils
- **Монтирования**: 
  - `./app` → `/app/app`
  - `./restart_xray.sh` → `/app/restart_xray.sh`
  - `./xray/config.json` → `/usr/local/etc/xray/config.json`
  - Docker socket для управления контейнерами

## 🚀 Команды управления

### Через Ansible (рекомендуется)
```bash
# Запустить все сервисы
./scripts/manage-servers.sh -a compose -c up

# Запустить с пересборкой
./scripts/manage-servers.sh -a compose -c up -b

# Остановить сервисы
./scripts/manage-servers.sh -a compose -c down

# Перезапустить сервисы
./scripts/manage-servers.sh -a compose -c restart

# Показать статус
./scripts/manage-servers.sh -a compose -c status

# Показать логи
./scripts/manage-servers.sh -a compose -c logs
```

### Прямые команды Ansible
```bash
# Запустить Docker Compose
ansible-playbook playbooks/docker-compose.yml -e "action=up"

# Запустить с пересборкой
ansible-playbook playbooks/docker-compose.yml -e "action=up" -e "build=true"

# Остановить
ansible-playbook playbooks/docker-compose.yml -e "action=down"

# Статус
ansible-playbook playbooks/docker-compose.yml -e "action=status"
```

### Прямые команды на сервере
```bash
# Подключиться к серверу
ssh root@176.97.67.100

# Перейти в директорию
cd /opt/fastapi_xray

# Запустить сервисы
docker-compose up -d --build

# Остановить сервисы
docker-compose down

# Показать статус
docker-compose ps

# Показать логи
docker-compose logs -f

# Перезапустить конкретный сервис
docker-compose restart fastapi
docker-compose restart xray
```

## 📁 Структура файлов

```
/opt/fastapi_xray/
├── docker-compose.yml          # Конфигурация Docker Compose
├── Dockerfile                  # Образ для FastAPI
├── requirements.txt            # Python зависимости
├── app/                        # FastAPI приложение
├── xray/
│   └── config.json            # Конфигурация Xray
├── squid/
│   └── passwd                 # Пароли для Squid
├── logs/
│   ├── xray/                  # Логи Xray
│   └── squid/                 # Логи Squid
└── restart_xray.sh            # Скрипт перезапуска Xray
```

## 🔍 Проверка работы

### 1. Проверить контейнеры
```bash
# На сервере
docker ps

# Через Ansible
ansible vpn_servers -m shell -a "docker ps"
```

### 2. Проверить логи
```bash
# Xray логи
docker logs xray

# FastAPI логи
docker logs fastapi

# Все логи
docker-compose logs
```

### 3. Проверить порты
```bash
# Проверить открытые порты
netstat -tlnp | grep -E ":(443|8081|8888)"

# Проверить доступность
curl http://localhost:8081/health
```

## ⚠️ Важные особенности

1. **Xray использует host network** - контейнер работает в сетевом пространстве хоста
2. **FastAPI монтирует Docker socket** - для управления другими контейнерами
3. **Автоматический перезапуск** - все контейнеры настроены на `restart: unless-stopped`
4. **Логи сохраняются** - все логи монтируются в директорию `./logs/`

## 🚨 Troubleshooting

### Проблемы с запуском
```bash
# Проверить статус Docker
systemctl status docker

# Проверить логи Docker
journalctl -u docker -f

# Перезапустить Docker
systemctl restart docker
```

### Проблемы с контейнерами
```bash
# Удалить все контейнеры
docker-compose down --volumes --remove-orphans

# Пересобрать образы
docker-compose build --no-cache

# Запустить заново
docker-compose up -d
```

### Проблемы с портами
```bash
# Проверить занятые порты
lsof -i :443
lsof -i :8081
lsof -i :8888

# Освободить порт
kill -9 $(lsof -t -i:8081)
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте статус: `./scripts/manage-servers.sh -a compose -c status`
2. Посмотрите логи: `./scripts/manage-servers.sh -a compose -c logs`
3. Перезапустите сервисы: `./scripts/manage-servers.sh -a compose -c restart`

---

**Готово!** 🎉 Docker Compose полностью интегрирован в Ansible и готов к работе.
