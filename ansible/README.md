# Ansible Configuration for FastAPI Xray VPN Service

Этот репозиторий содержит полную Ansible конфигурацию для развертывания и управления FastAPI Xray VPN сервисом.

## Структура проекта

```
ansible/
├── ansible.cfg                 # Основная конфигурация Ansible
├── requirements.yml            # Ansible Galaxy зависимости
├── requirements.txt            # Python зависимости
├── inventory/
│   └── hosts.yml              # Инвентарь серверов
├── group_vars/
│   ├── all.yml                # Глобальные переменные
│   └── vpn_servers.yml        # Переменные для VPN серверов
├── playbooks/
│   ├── deploy.yml             # Основной playbook для развертывания
│   ├── update.yml             # Playbook для обновления
│   ├── backup.yml             # Playbook для резервного копирования
│   └── restore.yml            # Playbook для восстановления
└── roles/
    ├── docker/                # Роль для установки Docker
    ├── nginx/                 # Роль для настройки Nginx
    ├── ssl/                   # Роль для SSL сертификатов
    ├── firewall/              # Роль для настройки firewall
    ├── xray/                  # Роль для настройки Xray
    ├── fastapi/               # Роль для настройки FastAPI
    └── squid/                 # Роль для настройки Squid
```

## Предварительные требования

### На управляющей машине (Ansible Control Node)

1. **Python 3.8+**
2. **Ansible 6.0+**
3. **Docker и Docker Compose** (для локального тестирования)

### На целевых серверах

1. **Ubuntu 20.04+** (рекомендуется 22.04 LTS)
2. **SSH доступ с root правами**
3. **Интернет соединение**

## Установка

### 1. Клонирование репозитория

```bash
git clone <your-repo-url>
cd fastapi_xray/ansible
```

### 2. Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Установка Ansible Galaxy зависимостей
ansible-galaxy install -r requirements.yml
```

### 3. Настройка инвентаря

Отредактируйте файл `inventory/hosts.yml`:

```yaml
vpn_servers:
  hosts:
    vpn-server-1:
      ansible_host: YOUR_SERVER_IP
      ansible_user: root
      ansible_ssh_private_key_file: ~/.ssh/id_rsa
      domain: your-domain.com
```

### 4. Настройка переменных

Отредактируйте файлы в `group_vars/`:

- `all.yml` - глобальные настройки
- `vpn_servers.yml` - настройки для VPN серверов

## Использование

### Развертывание

```bash
# Полное развертывание на всех серверах
ansible-playbook playbooks/deploy.yml

# Развертывание на конкретном сервере
ansible-playbook playbooks/deploy.yml --limit vpn-server-1

# Развертывание с тегами
ansible-playbook playbooks/deploy.yml --tags "docker,nginx"
```

### Обновление

```bash
# Обновление приложения
ansible-playbook playbooks/update.yml
```

### Резервное копирование

```bash
# Создание резервной копии
ansible-playbook playbooks/backup.yml
```

### Восстановление

```bash
# Восстановление из резервной копии
ansible-playbook playbooks/restore.yml
```

## Теги

Используйте теги для выполнения конкретных задач:

```bash
# Только Docker
ansible-playbook playbooks/deploy.yml --tags "docker"

# Только Nginx
ansible-playbook playbooks/deploy.yml --tags "nginx"

# Только SSL
ansible-playbook playbooks/deploy.yml --tags "ssl"

# Только Xray
ansible-playbook playbooks/deploy.yml --tags "xray"

# Только FastAPI
ansible-playbook playbooks/deploy.yml --tags "fastapi"

# Только Squid
ansible-playbook playbooks/deploy.yml --tags "squid"

# Только Firewall
ansible-playbook playbooks/deploy.yml --tags "firewall"
```

## Переменные

### Основные переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `domain` | Домен сервера | - |
| `xray_port` | Порт Xray | 443 |
| `fastapi_port` | Порт FastAPI | 8081 |
| `squid_port` | Порт Squid | 8888 |
| `ssl_email` | Email для SSL сертификата | - |

### Xray переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `xray_client_id` | UUID клиента | 960f001f-d065-410e-8a0d-c8aa2af4fe42 |
| `xray_private_key` | Приватный ключ Reality | - |
| `xray_public_key` | Публичный ключ Reality | - |
| `xray_short_id` | Короткий ID | f6213f68 |

## Безопасность

### Firewall

Ansible автоматически настраивает UFW с правилами:
- SSH (22)
- HTTP (80)
- HTTPS (443)
- FastAPI (8081)
- Squid (8888)

### Fail2ban

Настроен для защиты от:
- SSH брутфорса
- Nginx атак
- HTTP атак

### SSL

Автоматическое получение и обновление SSL сертификатов через Let's Encrypt.

## Мониторинг

### Логи

Логи сервисов сохраняются в:
- `/opt/fastapi_xray/logs/xray/`
- `/opt/fastapi_xray/logs/squid/`
- `/var/log/nginx/`

### Health Checks

- FastAPI: `http://your-domain:8081/health`
- Nginx: `http://your-domain/health`

## Troubleshooting

### Проверка статуса сервисов

```bash
# На сервере
systemctl status xray fastapi squid nginx

# Через Ansible
ansible vpn_servers -m systemd -a "name=xray"
```

### Просмотр логов

```bash
# Xray логи
tail -f /opt/fastapi_xray/logs/xray/access.log
tail -f /opt/fastapi_xray/logs/xray/error.log

# Nginx логи
tail -f /var/log/nginx/fastapi_access.log
tail -f /var/log/nginx/fastapi_error.log
```

### Перезапуск сервисов

```bash
# Через Ansible
ansible vpn_servers -m systemd -a "name=xray state=restarted"

# На сервере
systemctl restart xray fastapi squid nginx
```

## Поддержка

При возникновении проблем:

1. Проверьте логи сервисов
2. Убедитесь в правильности переменных
3. Проверьте доступность портов
4. Проверьте SSL сертификаты

## Лицензия

MIT License
