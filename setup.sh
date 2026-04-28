#!/bin/bash

echo "جارٍ تثبيت المتطلبات..."
pip install -r requirements.txt

echo "إنشاء قاعدة البيانات..."
python manage.py makemigrations
python manage.py migrate

echo "إنشاء المستخدم المدير..."
python create_admin.py

echo "جمع الملفات الثابتة..."
python manage.py collectstatic --noinput

echo "تم التثبيت بنجاح!"
echo "لتشغيل الخادم: python manage.py runserver"
