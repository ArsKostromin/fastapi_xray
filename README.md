# My FastAPI Project

---

````markdown
# 🚀 FastAPI Backend Template

Полностью готовая основа для запуска FastAPI-проекта на Ubuntu 22.04+ с Docker, Nginx, Certbot и базовыми тулзами.

---

## 🔧 Установка базового софта

Установим всё необходимое: системные утилиты, Git, Nginx и откроем нужные порты:

```bash
sudo apt update && sudo apt upgrade -y

# Утилиты
sudo apt install -y nano curl wget zip unzip tar lsb-release gnupg \
  apt-transport-https ca-certificates software-properties-common \
  net-tools htop ufw

# Git
sudo apt install -y git

# Nginx
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Открываем порты 80 и 443
sudo ufw allow 'Nginx Full'
````

---

## 🐳 Установка Docker + Docker Compose

```bash
# Удалим старые версии
sudo apt remove -y docker docker-engine docker.io containerd runc

# Добавим репозиторий Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Устанавливаем Docker и Compose
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Проверим установку
sudo docker version
```

📦 Чтобы использовать `docker` без `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🐍 Установка Python 3 + pip (если нужно)

```bash
sudo apt install -y python3 python3-pip python3-venv
```

---

## 🔐 Let's Encrypt + Certbot (SSL)

Устанавливаем Certbot и получаем SSL-сертификат через standalone режим (без Nginx):

```bash
# Установка
sudo apt install -y certbot python3-certbot-nginx

# Останавливаем Nginx, если нужно
sudo systemctl stop nginx

# Получаем сертификат
sudo certbot certonly --standalone -d united-kingdom.server2.anonixvpn.space

# После получения — можно стартануть nginx обратно
sudo systemctl start nginx
```

🎯 Сертификаты будут находиться здесь:

```
/etc/letsencrypt/live/united-kingdom.server2.anonixvpn.space/fullchain.pem
/etc/letsencrypt/live/united-kingdom.server2.anonixvpn.space/privkey.pem
```

---

## 🔄 Автообновление сертификатов

Certbot автоматически настраивает `systemd`-таймер. Проверка:

```bash
sudo systemctl list-timers | grep certbot
```

Ручная проверка продления:

```bash
sudo certbot renew --dry-run
```

---

## 🧩 Дополнительно

* 🛡 **Fail2ban** — простая защита от брутфорса:

```bash
sudo apt install -y fail2ban
```

---

## 📦 Пример запуска FastAPI-проекта в Docker

Создай `docker-compose.yml` и `Dockerfile` (не включены в этот README), затем:

```bash
sudo docker compose up -d --build
```

---

## 🧠 Полезные команды

```bash
# Перезапуск nginx
sudo systemctl restart nginx

# Проверка SSL-сертификата
openssl x509 -in /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem -noout -dates

# Проверка статуса certbot
sudo certbot certificates
```

---

💬 Если ты дошёл до сюда — у тебя уже в руках полноценная платформа для деплоя микросервисов, VPN-ботов, админок и чего угодно на FastAPI.

---

> ⛩️ *"Тот, кто хочет защитить свой сервер — начинает с firewall.
> Но тот, кто хочет жить долго — ставит certbot."* — древняя китайская пословица.

```

---

Хочешь — сгенерю и `Dockerfile`, `docker-compose.yml` или шаблон для FastAPI `main.py`.
```
