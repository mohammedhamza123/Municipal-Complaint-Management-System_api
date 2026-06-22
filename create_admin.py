"""
Script to create admin superuser account
"""
import requests
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# API Configuration
BASE_URL = "http://localhost:8000"

# Admin account details
admin_data = {
    "email": "admin@municipality.gov",
    "username": "admin",
    "password": "admin123",
    "full_name": "مدير النظام الرئيسي",
    "is_active": True,
    "is_superuser": True
}

def create_admin():
    """Create admin superuser account"""
    try:
        # First, try to register the admin user
        response = requests.post(
            f"{BASE_URL}/auth/register",
            data=admin_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 201:
            print("✅ تم إنشاء حساب الإدمن الرئيسي بنجاح!")
            print(f"\n📧 البريد الإلكتروني: {admin_data['email']}")
            print(f"👤 اسم المستخدم: {admin_data['username']}")
            print(f"🔑 كلمة المرور: {admin_data['password']}")
            print(f"👑 إدمن رئيسي: نعم")
            return True
        elif response.status_code == 400:
            # User might already exist, try to login
            print("⚠️  الحساب موجود بالفعل. جاري محاولة تسجيل الدخول...")
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                data={
                    "username": admin_data["email"],
                    "password": admin_data["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if login_response.status_code == 200:
                print("✅ الحساب موجود ويمكن تسجيل الدخول به!")
                print(f"\n📧 البريد الإلكتروني: {admin_data['email']}")
                print(f"👤 اسم المستخدم: {admin_data['username']}")
                print(f"🔑 كلمة المرور: {admin_data['password']}")
                return True
            else:
                print(f"❌ خطأ في تسجيل الدخول: {login_response.text}")
                return False
        else:
            print(f"❌ خطأ في إنشاء الحساب: {response.status_code}")
            print(f"الرد: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ خطأ: لا يمكن الاتصال بالخادم. تأكد من أن Backend يعمل على http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  إنشاء حساب مدير النظام الرئيسي")
    print("=" * 60)
    print()
    
    create_admin()
    
    print()
    print("=" * 60)
    print("  يمكنك الآن تسجيل الدخول باستخدام:")
    print(f"  📧 البريد: {admin_data['email']}")
    print(f"  🔑 كلمة المرور: {admin_data['password']}")
    print("=" * 60)

