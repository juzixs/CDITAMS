import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]

print('现有表:')
for t in tables:
    print(f'  {t}')
print()

needed = ['software_field_values', 'software_license']
for table in needed:
    if table in tables:
        print(f'存在: {table}')
    else:
        print(f'缺失: {table}')