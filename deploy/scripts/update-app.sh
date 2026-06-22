#!/usr/bin/env bash
# تحديث التطبيق بعد رفع نسخة جديدة
set -euo pipefail

APP_DIR="/var/www/municipal-api"
cd "${APP_DIR}"

echo "==> تفعيل البيئة الافتراضية..."
source venv/bin/activate

echo "==> تثبيت/تحديث التبعيات..."
pip install -r requirements.txt

echo "==> إعادة تشغيل الخدمة..."
sudo systemctl restart municipal-api

echo "==> التحقق من الحالة..."
sleep 2
curl -sf http://127.0.0.1:8000/health && echo "" && echo "✓ API يعمل بنجاح" || {
  echo "✗ فشل health check — راجع السجلات: sudo journalctl -u municipal-api -n 50"
  exit 1
}
