# 🚀 FastAPI Xray VPN Service - Настройка серверов

## 📋 Список серверов

| Страна | Сервер | IP адрес | Пароль |
|--------|--------|----------|--------|
| 🇦🇪 ОАЭ | uae-server | 176.97.67.100 | soS3YxA462 |
| 🇧🇷 Бразилия | brazil-server | 38.180.220.125 | Ggyj4A6UuG |
| 🇩🇪 Германия | germany-server | 37.1.199.23 | Fwq7nMJ3r9 |
| 🇯🇵 Япония | japan-server | 176.97.71.56 | 7FUH9RkfsH |
| 🇹🇷 Турция | turkey-server | 5.180.45.191 | YMy5iXE6ydtA |
| 🇪🇸 Испания | spain-server | 45.12.150.217 | I2tx1v8E5hj7 |
| 🇦🇺 Австралия | australia-server | 45.15.185.58 | l9Z4ocxec58x |
| 🇺🇸 США | usa-server | 94.131.101.213 | yV5w6rUsy9FR |

## 🛠 Быстрый старт

### 1. Установка Ansible

```bash
cd fastapi_xray/ansible
./scripts/install.sh
```

### 2. Проверка подключения

```bash
./scripts/manage-servers.sh -a check
```

### 3. Развертывание на всех серверах

```bash
./scripts/manage-servers.sh -a deploy
```

## 📖 Подробные команды

### Проверка подключения
```bash
# Проверить все серверы
./scripts/manage-servers.sh -a check

# Проверить конкретный сервер
./scripts/manage-servers.sh -a check -l uae-server
```

### Развертывание
```bash
# Развернуть на всех серверах
./scripts/manage-servers.sh -a deploy

# Развернуть на конкретном сервере
./scripts/manage-servers.sh -a deploy -l germany-server

# Развернуть только Docker и Nginx
./scripts/manage-servers.sh -a deploy -t docker,nginx

# Тестовый запуск (без изменений)
./scripts/manage-servers.sh -a deploy -d
```

### Управление сервисами
```bash
# Проверить статус всех сервисов
./scripts/manage-servers.sh -a status

# Перезапустить все сервисы
./scripts/manage-servers.sh -a restart

# Посмотреть логи
./scripts/manage-servers.sh -a logs
```

### Обновление и резервное копирование
```bash
# Обновить все серверы
./scripts/manage-servers.sh -a update

# Создать резервные копии
./scripts/manage-servers.sh -a backup
```

## 🔧 Прямые команды Ansible

### Проверка подключения
```bash
ansible-playbook playbooks/check-connectivity.yml
```

### Развертывание
```bash
# Все серверы
ansible-playbook playbooks/deploy-all.yml

# Конкретный сервер
ansible-playbook playbooks/deploy-all.yml --limit uae-server

# С тегами
ansible-playbook playbooks/deploy-all.yml --tags docker,nginx
```

### Управление сервисами
```bash
# Проверить статус Xray
ansible vpn_servers -m systemd -a "name=xray"

# Перезапустить FastAPI
ansible vpn_servers -m systemd -a "name=fastapi state=restarted"

# Посмотреть логи
ansible vpn_servers -m shell -a "tail -f /opt/fastapi_xray/logs/xray/access.log"
```

## 🌐 Доступ к сервисам

После развертывания сервисы будут доступны по адресам:

- **FastAPI API**: `http://IP:8081`
- **Xray VPN**: `IP:443`
- **Squid Proxy**: `IP:8888`
- **Nginx (HTTP)**: `http://IP`

### Примеры доступа:
- **ОАЭ**: `http://176.97.67.100:8081` (FastAPI), `176.97.67.100:443` (Xray)
- **Бразилия**: `http://38.180.220.125:8081` (FastAPI), `38.180.220.125:443` (Xray)
- **Германия**: `http://37.1.199.23:8081` (FastAPI), `37.1.199.23:443` (Xray)
- **Япония**: `http://176.97.71.56:8081` (FastAPI), `176.97.71.56:443` (Xray)
- **Турция**: `http://5.180.45.191:8081` (FastAPI), `5.180.45.191:443` (Xray)
- **Испания**: `http://45.12.150.217:8081` (FastAPI), `45.12.150.217:443` (Xray)
- **Австралия**: `http://45.15.185.58:8081` (FastAPI), `45.15.185.58:443` (Xray)
- **США**: `http://94.131.101.213:8081` (FastAPI), `94.131.101.213:443` (Xray)

## 🔐 Работа без доменов

Конфигурация настроена для работы только по IP адресам:

- **SSL сертификаты отключены** (так как без доменов их получить нельзя)
- **Nginx работает только по HTTP** (порт 80)
- **Все сервисы доступны напрямую по IP**
- **Xray VPN работает по Reality протоколу** (не требует SSL)

## 📁 Структура конфигурации

```
ansible/
├── inventory/hosts.yml          # Список всех серверов
├── host_vars/                   # Индивидуальные настройки серверов
│   ├── uae-server.yml
│   ├── brazil-server.yml
│   ├── germany-server.yml
│   ├── japan-server.yml
│   ├── turkey-server.yml
│   ├── spain-server.yml
│   ├── australia-server.yml
│   └── usa-server.yml
├── group_vars/                  # Общие настройки
│   ├── all.yml
│   └── vpn_servers.yml
├── playbooks/                   # Playbook'и для развертывания
│   ├── deploy-all.yml
│   ├── check-connectivity.yml
│   ├── update.yml
│   ├── backup.yml
│   └── restore.yml
└── scripts/                     # Скрипты управления
    ├── install.sh
    ├── deploy.sh
    └── manage-servers.sh
```

## 🚨 Важные замечания

1. **Пароли**: Все пароли сохранены в inventory файле. Рекомендуется использовать SSH ключи вместо паролей.

2. **Без доменов**: Конфигурация работает только по IP адресам, SSL отключен.

3. **HTTP только**: Nginx работает только по HTTP (порт 80), HTTPS недоступен.

4. **Firewall**: Автоматически настраивается UFW с правилами для всех необходимых портов.

5. **Логи**: Все логи сохраняются в `/opt/fastapi_xray/logs/` на каждом сервере.

6. **Xray Reality**: VPN работает по Reality протоколу, который не требует SSL сертификатов.

## 🔍 Troubleshooting

### Проблемы с подключением
```bash
# Проверить SSH подключение
ssh root@176.97.67.100

# Проверить через Ansible
ansible uae-server -m ping
```

### Проблемы с сервисами
```bash
# Проверить статус на сервере
systemctl status xray fastapi squid nginx

# Посмотреть логи
journalctl -u xray -f
docker logs fastapi
```

### Проблемы с сервисами
```bash
# Проверить статус всех сервисов
systemctl status xray fastapi squid nginx

# Перезапустить сервисы
systemctl restart xray fastapi squid nginx
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи сервисов
2. Убедитесь в правильности DNS записей
3. Проверьте доступность портов
4. Проверьте SSL сертификаты

---

**Готово!** 🎉 Теперь у вас есть полностью настроенная инфраструктура VPN серверов в 8 странах мира.
