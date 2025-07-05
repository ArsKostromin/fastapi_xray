#!/bin/bash

set -e

if [ -z "$1" ]; then
  echo -e "\n❌ Укажи домен как аргумент: ./install_squid.sh <domain>"
  exit 1
fi

DOMAIN="$1"
UUID=$(uuidgen)
PASS="x"

echo "📦 Устанавливаем Squid..."
apt update && apt install -y squid apache2-utils

echo "🛠 Настраиваем Squid..."
cat > /etc/squid/squid.conf <<EOF
http_port 127.0.0.1:8888

# Аутентификация
auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic children 5
auth_param basic realm Squid proxy
auth_param basic credentialsttl 2 hours
auth_param basic casesensitive on

# ACL по логину
acl localnet src 127.0.0.1
acl authenticated proxy_auth REQUIRED

http_access allow localnet authenticated
http_access deny all

logformat mailformat %ts.%03tu %>a %un %rm %ru %>Hs
access_log /var/log/squid/access.log mailformat

cache_log /var/log/squid/cache.log

via off
forwarded_for delete
EOF

echo "🔐 Создаём юзера для Squid: $UUID:$PASS"
htpasswd -cb /etc/squid/passwd "$UUID" "$PASS"

echo "🔁 Перезапуск Squid..."
systemctl enable squid --now
systemctl restart squid

echo -e "\n✅ Squid установлен и запущен"
echo "🧑‍💻 Логин: $UUID"
echo "🔑 Пароль: $PASS"
echo "📡 Домен: $DOMAIN"