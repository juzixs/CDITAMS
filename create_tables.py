import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from django.db import connection

# 创建 software_field_values 表
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS software_field_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER NOT NULL,
        field_id INTEGER NOT NULL,
        value TEXT DEFAULT ''
    )
''')
print('已创建 software_field_values 表')

# 创建 software_licenses 表 (如果不存在)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS software_licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        software_id INTEGER NOT NULL,
        user_id INTEGER,
        license_key TEXT,
        assigned_date TEXT,
        expiry_date TEXT,
        is_active INTEGER DEFAULT 1
    )
''')
print('已创建 software_licenses 表')

connection.commit()
print('完成!')