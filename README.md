# 驰达IT资产管理系统 (CDITAMS)

CDITAMS是一个基于Flask的IT资产管理系统，旨在帮助企业高效管理IT资产。

## 功能特点

- 响应式设计，支持PC、手机、平板等多种设备
- 模块化架构，包含主页、待办、资产、盘点、组织、设置、日志等模块
- 完善的权限控制系统，基于角色的权限管理
- 用户、部门、角色管理功能

## 安装与运行

1. 克隆项目代码
```
git clone <repository-url>
cd CDITAMS
```

2. 创建虚拟环境并安装依赖
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 运行应用
```
python run.py
```

4. 在浏览器中访问 `http://127.0.0.1:5000`

## 默认账号

- 工号: 86000001
- 密码: password
- 角色: 超级管理员

## 技术栈

- 后端: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- 前端: Bootstrap 5, jQuery, Font Awesome
- 数据库: SQLite (开发), 可扩展至MySQL/PostgreSQL等

## 项目结构

```
CDITAMS/
├── app/                 # 应用主目录
│   ├── models/          # 数据模型
│   ├── static/          # 静态文件 (CSS, JS, 图片)
│   ├── templates/       # 模板文件
│   ├── utils/           # 工具函数
│   ├── views/           # 视图函数
│   └── __init__.py      # 应用初始化
├── run.py               # 应用入口
└── requirements.txt     # 项目依赖
```

## 开发计划

- [x] 用户认证与权限管理
- [x] 组织架构管理(用户、部门、角色)
- [ ] 资产管理
- [ ] 盘点管理
- [ ] 待办系统
- [ ] 日志管理
- [ ] 系统设置

## 许可证

© 2023 驰达集团 