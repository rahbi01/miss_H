import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiking_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from hiking.models import UserProfile

def create_admin():
    username = 'admin'
    password = '123'  # غير هذا في الإنتاج
    
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username=username, password=password, email='admin@example.com')
        UserProfile.objects.create(user=user, role='admin')
        print(f"تم إنشاء المستخدم المدير: {username} / كلمة المرور: {password}")
    else:
        print("المستخدم موجود بالفعل")

if __name__ == '__main__':
    create_admin()
