#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库表结构
"""

import os
import sys

# 确保能够导入模型
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models.user import User
from app.models.task import Task

# 输出当前引擎信息
print(f"数据库引擎: {engine.url}")
print(f"Python版本: {sys.version}")

# 检查表结构是否存在
from sqlalchemy import inspect
inspector = inspect(engine)

# 检查所有表
print("\n当前数据库中的表:")
for table in inspector.get_table_names():
    print(f"- {table}")

# 检查 users 表是否存在
if 'users' in inspector.get_table_names():
    print("\nusers 表已存在")
else:
    print("\nusers 表不存在，将创建新表")

# 检查 tasks 表是否存在
if 'tasks' in inspector.get_table_names():
    print("\ntasks 表已存在，检查列结构:")
    columns = inspector.get_columns('tasks')
    for column in columns:
        if column['name'] == 'result_data':
            print(f"result_data 列类型: {column['type']}")
            break
else:
    print("\ntasks 表不存在，将创建新表")

# 更新表结构
print("\n更新表结构...")
try:
    # 先删除现有表（仅用于开发环境）
    if 'tasks' in inspector.get_table_names():
        print("删除现有 tasks 表...")
        Task.__table__.drop(engine, checkfirst=True)
        print("已删除现有 tasks 表")
    
    # 重新创建表
    print("创建表结构...")
    Base.metadata.create_all(bind=engine)
    print("表结构更新成功！")
except Exception as e:
    print(f"更新表结构失败: {e}")
    import traceback
    traceback.print_exc()

# 验证更新结果
print("\n验证更新结果:")
inspector = inspect(engine)  # 重新获取 inspector
if 'tasks' in inspector.get_table_names():
    print("tasks 表已创建")
    columns = inspector.get_columns('tasks')
    for column in columns:
        if column['name'] == 'result_data':
            print(f"result_data 列类型: {column['type']}")
            break
else:
    print("tasks 表不存在")

# 再次检查所有表
print("\n更新后的数据库中的表:")
for table in inspector.get_table_names():
    print(f"- {table}")