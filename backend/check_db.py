#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import pymysql
import os
import sys
import re

# 确保能够导入 settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"脚本路径: {os.path.abspath(__file__)}")

# 尝试导入 settings
try:
    from app.core.config import settings
    print("成功导入 settings")
except Exception as e:
    print(f"导入 settings 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 解析数据库连接字符串
db_url = settings.DATABASE_URL
# 从URL中提取数据库连接信息
# 格式: mysql+pymysql://user:password@host:port/dbname
import urllib.parse
parsed_url = urllib.parse.urlparse(db_url)
db_user = parsed_url.username
db_password = parsed_url.password
db_host = parsed_url.hostname
db_port = parsed_url.port or 3306
db_name = parsed_url.path[1:]  # 去掉开头的 '/' 字符

print(f"连接到数据库: {db_host}:{db_port}/{db_name}")
print(f"用户名: {db_user}")
print(f"密码长度: {len(db_password) if db_password else 0}")

# 连接数据库
try:
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("数据库连接成功")
    
    with conn.cursor() as cursor:
        # 获取所有表
        print("\n获取所有表...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\n当前数据库中的表 ({len(tables)} 个):")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"- {table_name}")
        
        # 检查每个表的结构
        for table in tables:
            table_name = list(table.values())[0]
            print(f"\n表 {table_name} 的结构:")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            # 打印列信息
            for column in columns:
                null_status = "NOT NULL" if column['Null'] == 'NO' else "NULL"
                key_status = f" {column['Key']}" if column['Key'] else ""
                default_value = f" DEFAULT {column['Default']}" if column['Default'] is not None else ""
                print(f"  {column['Field']}: {column['Type']} {null_status}{key_status}{default_value}")
            
            # 检查外键
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table_sql = cursor.fetchone()['Create Table']
            if 'FOREIGN KEY' in create_table_sql:
                print("  外键约束:")
                # 提取外键信息
                foreign_keys = re.findall(r'FOREIGN KEY \(([^)]+)\) REFERENCES ([^\(]+)\(([^)]+)\)', create_table_sql)
                for fk in foreign_keys:
                    print(f"    {fk[0]} -> {fk[1]}({fk[2]})")
    
    conn.close()
    print("\n数据库连接已关闭")
except Exception as e:
    print(f"数据库连接失败: {e}")
    import traceback
    traceback.print_exc()