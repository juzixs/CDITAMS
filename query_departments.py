from app import create_app
from app.models.department import Department

app = create_app()
with app.app_context():
    print('部门数据:')
    departments = Department.query.all()
    if departments:
        for dept in departments:
            parent_name = f"(父部门: {dept.parent.name})" if dept.parent else "(无父部门)"
            print(f"ID: {dept.id}, 名称: {dept.name}, 编码: {dept.code}, {parent_name}")
    else:
        print("数据库中没有部门记录") 