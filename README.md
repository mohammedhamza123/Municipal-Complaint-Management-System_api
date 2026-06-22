# Municipal Complaint Management System — API

باك اند FastAPI لنظام إدارة شكاوى البلدية، مع **SQLite** (`municipal_complaints.db`) جاهزة للنشر.

## المحتويات

| المجلد/الملف | الوصف |
|--------------|--------|
| `src/` | كود API |
| `municipal_complaints.db` | قاعدة SQLite مع بيانات المستخدمين |
| `requirements.txt` | تبعيات Python |
| `.env.example` | نموذج إعدادات البيئة |
| `deploy/` | Nginx + systemd + سكربتات النشر |
| `uploads/` | مجلد الصور المرفوعة |

## التشغيل المحلي

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux:   source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `http://127.0.0.1:8000/health`
- Docs: `http://127.0.0.1:8000/docs`

## النشر على VPS (SQLite)

```bash
sudo mkdir -p /var/www/municipal-api
sudo chown -R $USER:$USER /var/www/municipal-api
cd /var/www/municipal-api

git clone YOUR_REPO_URL .
cp .env.example .env
nano .env   # غيّر SECRET_KEY و WORKERS=1

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mkdir -p uploads/profiles uploads/complaints uploads/issues_resolved
sudo chown -R www-data:www-data /var/www/municipal-api
sudo chmod 664 municipal_complaints.db

sudo cp deploy/systemd/municipal-api.service /etc/systemd/system/
sudo cp deploy/nginx/municipal-api.conf /etc/nginx/sites-available/municipal-api
sudo ln -sf /etc/nginx/sites-available/municipal-api /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable --now municipal-api
sudo nginx -t && sudo systemctl reload nginx
```

## ملاحظات

- **لا ترفع** `.env` ولا `firebase-service-account.json` إلى Git.
- مع SQLite استخدم `WORKERS=1` في `.env`.
- بعد `git clone`، قاعدة البيانات موجودة — لا حاجة لتشغيل `seed` إلا لإعادة البيانات الافتراضية.

## مسح البيانات (مع الإبقاء على المستخدمين)

```bash
python -m src.core.clear_data
```
