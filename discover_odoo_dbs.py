#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo数据库发现工具
"""

import requests
import json

def discover_odoo_databases():
    """发现可用的Odoo数据库"""

    print("🔍 发现Odoo数据库...")
    print("=" * 40)

    url = "http://localhost:8069/web/database/list"

    try:
        # 获取数据库列表
        response = requests.post(url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({})
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                databases = result.get('result', [])
                print(f"✅ 找到 {len(databases)} 个数据库:")
                for i, db in enumerate(databases, 1):
                    print(f"  {i}. {db}")

                if databases:
                    print(f"\n💡 建议使用数据库名: {databases[0]}")
                    return databases
                else:
                    print("❌ 没有找到任何数据库")
                    return []
            else:
                print(f"❌ 获取数据库列表失败: {result}")
                return []
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return []

def test_database_connection(db_name):
    """测试特定数据库的连接"""
    print(f"\n🧪 测试数据库连接: {db_name}")
    print("-" * 30)

    url = "http://localhost:8069/web/session/authenticate"

    data = {
        "jsonrpc": "2.0",
        "params": {
            "db": db_name,
            "login": "admin",
            "password": "admin123"
        }
    }

    try:
        response = requests.post(url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('result'):
                print(f"✅ 数据库 {db_name} 连接成功!")
                session_info = result.get('result', {})
                user_info = session_info.get('uid')
                print(f"   用户ID: {user_info}")
                return True
            else:
                error = result.get('error', {})
                message = error.get('message', 'Unknown error')
                print(f"❌ 认证失败: {message}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 发现数据库
    databases = discover_odoo_databases()

    if databases:
        print("\n🧪 测试数据库连接...")
        for db in databases:
            test_database_connection(db)

        print(f"\n🎯 总结:")
        print(f"✅ 发现 {len(databases)} 个数据库")
        print("请使用正确的数据库名称更新测试脚本配置")
    else:
        print("\n🔧 建议:")
        print("1. 确保Odoo服务器正在运行")
        print("2. 检查端口8069是否可访问")
        print("3. 创建至少一个数据库")
        print("4. 或者使用Odoo界面查看实际的数据库名称")

    # 直接测试正确的数据库
    print("\n🧪 直接测试 odoo_dev 数据库...")
    test_database_connection('odoo_dev')