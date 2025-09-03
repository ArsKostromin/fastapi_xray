# 🪟 Установка Ansible на Windows

## 📋 Варианты установки

### Вариант 1: WSL2 (рекомендуется)

1. **Установите WSL2**:
   ```powershell
   wsl --install
   ```

2. **Установите Ubuntu в WSL**:
   ```powershell
   wsl --install -d Ubuntu
   ```

3. **В WSL Ubuntu выполните**:
   ```bash
   # Обновить систему
   sudo apt update && sudo apt upgrade -y
   
   # Установить Python и pip
   sudo apt install python3 python3-pip python3-venv -y
   
   # Перейти в директорию проекта
   cd /mnt/c/Users/arsya/Desktop/vpnservice/fastapi_xray/ansible
   
   # Запустить установочный скрипт
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

### Вариант 2: Git Bash + Python

1. **Установите Python 3.8+** с [python.org](https://www.python.org/downloads/)

2. **Установите Git Bash** с [git-scm.com](https://git-scm.com/download/win)

3. **Откройте Git Bash и выполните**:
   ```bash
   # Перейти в директорию проекта
   cd /c/Users/arsya/Desktop/vpnservice/fastapi_xray/ansible
   
   # Создать виртуальное окружение
   python -m venv venv
   source venv/Scripts/activate
   
   # Установить зависимости
   pip install -r requirements.txt
   
   # Установить Ansible Galaxy зависимости
   ansible-galaxy install -r requirements.yml
   ```

### Вариант 3: Docker Desktop

1. **Установите Docker Desktop** с [docker.com](https://www.docker.com/products/docker-desktop/)

2. **Создайте Dockerfile для Ansible**:
   ```dockerfile
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \
       openssh-client \
       git \
       && rm -rf /var/lib/apt/lists/*
   
   RUN pip install ansible docker
   
   WORKDIR /workspace
   ```

3. **Запустите контейнер**:
   ```bash
   docker run -it --rm -v ${PWD}:/workspace ansible-container
   ```

## 🚀 Быстрый старт

После установки Ansible:

### 1. Проверка подключения
```bash
# Активировать виртуальное окружение (если используете)
source venv/bin/activate  # Linux/WSL
# или
source venv/Scripts/activate  # Windows Git Bash

# Проверить подключение ко всем серверам
./scripts/manage-servers.sh -a check
```

### 2. Развертывание
```bash
# Развернуть на всех серверах
./scripts/manage-servers.sh -a deploy

# Развернуть на конкретном сервере
./scripts/manage-servers.sh -a deploy -l uae-server
```

## 🔧 Настройка SSH ключей (опционально)

Для удобства можно настроить SSH ключи вместо паролей:

### 1. Сгенерировать SSH ключ
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

### 2. Скопировать публичный ключ на серверы
```bash
# Для каждого сервера
ssh-copy-id root@176.97.67.100
ssh-copy-id root@38.180.220.125
# и т.д.
```

### 3. Обновить inventory
Заменить `ansible_ssh_pass` на `ansible_ssh_private_key_file: ~/.ssh/id_rsa`

## 📁 Структура проекта

```
fastapi_xray/ansible/
├── scripts/
│   ├── install.sh          # Установка Ansible
│   └── manage-servers.sh   # Управление серверами
├── inventory/
│   └── hosts.yml           # Список серверов
├── playbooks/
│   ├── deploy-no-ssl.yml   # Развертывание
│   └── check-connectivity.yml
├── roles/                  # Роли Ansible
├── host_vars/              # Настройки серверов
└── group_vars/             # Общие настройки
```

## 🎯 Команды управления

```bash
# Проверить подключение
./scripts/manage-servers.sh -a check

# Развернуть на всех серверах
./scripts/manage-servers.sh -a deploy

# Развернуть на конкретном сервере
./scripts/manage-servers.sh -a deploy -l uae-server

# Проверить статус
./scripts/manage-servers.sh -a status

# Посмотреть логи
./scripts/manage-servers.sh -a logs

# Управлять Docker Compose
./scripts/manage-servers.sh -a compose -c up -b
```

## ⚠️ Важные замечания

1. **Пароли в inventory** - все пароли серверов уже настроены в `inventory/hosts.yml`
2. **Безопасность** - рекомендуется использовать SSH ключи вместо паролей
3. **Firewall** - убедитесь, что порт 22 (SSH) открыт на всех серверах
4. **Интернет** - Ansible должен иметь доступ к интернету для установки пакетов

## 🔍 Troubleshooting

### Проблемы с подключением
```bash
# Проверить SSH подключение вручную
ssh root@176.97.67.100

# Проверить через Ansible
ansible uae-server -m ping
```

### Проблемы с правами
```bash
# Установить права на скрипты
chmod +x scripts/*.sh
```

### Проблемы с Python
```bash
# Переустановить виртуальное окружение
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

**Готово!** 🎉 Теперь вы можете управлять всеми 8 серверами с вашего ПК!
