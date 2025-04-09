from app import create_app, db
from app.models.department import Department
import traceback

app = create_app()
with app.app_context():
    try:
        print('部门数据:')
        departments = Department.query.all()
        if departments:
            for dept in departments:
                parent_name = f"(父部门: {dept.parent.name})" if dept.parent else "(无父部门)"
                print(f"ID: {dept.id}, 名称: {dept.name}, 编码: {dept.code}, {parent_name}")
        else:
            print("数据库中没有部门记录")
            
        # 尝试添加一个测试部门
        print("\n尝试添加测试部门...")
        test_dept = Department(name="测试部门", code="TEST")
        db.session.add(test_dept)
        db.session.commit()
        print("测试部门添加成功")
        
        # 再次查询确认
        print("\n添加后的部门数据:")
        for dept in Department.query.all():
            parent_name = f"(父部门: {dept.parent.name})" if dept.parent else "(无父部门)"
            print(f"ID: {dept.id}, 名称: {dept.name}, 编码: {dept.code}, {parent_name}")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print(traceback.format_exc()) 