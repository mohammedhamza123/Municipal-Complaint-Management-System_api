#!/usr/bin/env bash
# إعداد أولي للسيرفر — Ubuntu/Debian + SQLite
set -euo pipefail

APP_DIR="/var/www/municipal-api"

echo "==> تثبيت الحزم الأساسية..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git ufw sqlite3

echo "==> إنشاء مجلد التطبيق..."
sudo mkdir -p "${APP_DIR}"
sudo chown -R "$USER":"$USER" "${APP_DIR}"

echo "==> تفعيل الجدار الناري..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo ""
echo "✓ اكتمل الإعداد الأولي."
echo "  1. انسخ/clone المشروع إلى: ${APP_DIR}"
echo "  2. تأكد من وجود municipal_complaints.db في المجلد"
echo "  3. أنشئ .env من .env.example وعدّل SECRET_KEY"
echo "  4. cd ${APP_DIR} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "  5. mkdir -p uploads/profiles uploads/complaints uploads/issues_resolved"
echo "  6. sudo chown -R www-data:www-data ${APP_DIR}"
echo "  7. systemd + nginx (راجع README.md)"
