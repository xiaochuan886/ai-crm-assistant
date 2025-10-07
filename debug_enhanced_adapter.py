#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Enhanced适配器的连接问题
"""

import sys
import os
import requests
import json
from urllib.parse import urljoin

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_enhanced_connection():
    """调试Enhanced适配器的连接问题"""

    print("🔍 调试Enhanced Odoo连接...")
    print("=" * 40)

    # 基本配置
    base_url = "http://localhost:8069"
    db = "odoo_dev"
    username = "admin"
    password = "admin123"

    try:
        # 1. 测试认证
        print("1️⃣ 测试认证...")
        session = requests.Session()

        login_url = f"{base_url}/web/session/authenticate"
        login_data = {
            'jsonrpc': '2.0',
            'params': {
                'db': db,
                'login': username,
                'password': password,
            }
        }

        response = session.post(login_url, json=login_data, timeout=30)
        print(f"认证响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get('result'):
                uid = result['result']['uid']
                context = result['result'].get('user_context', {})
                print(f"✅ 认证成功! UID: {uid}")

                # 保存session
                session_id = response.cookies.get('session_id')
                if session_id:
                    session.cookies.set('session_id', session_id)
                    print(f"✅ Session ID: {session_id}")

                # 2. 测试简单的read方法
                print("\n2️⃣ 测试简单的read方法...")
                rpc_url = f"{base_url}/web/dataset/call_kw"

                # 测试read方法
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': 'res.users',
                        'method': 'read',
                        'args': [[uid]],
                        'kwargs': {
                            'context': context,
                            'fields': ['name', 'login', 'email']
                        }
                    },
                    'id': 1
                }

                response = session.post(rpc_url, json=rpc_data)
                print(f"Read响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('result'):
                        user_data = result['result'][0]
                        print(f"✅ Read成功: {user_data}")
                    else:
                        print(f"❌ Read失败: {result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Read请求失败: {response.status_code}")
                    print(f"响应内容: {response.text}")

                # 3. 测试search_read方法
                print("\n3️⃣ 测试search_read方法...")
                search_rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': 'res.users',
                        'method': 'search_read',
                        'args': [],  # 添加空的args参数
                        'kwargs': {
                            'domain': [['id', '=', uid]],
                            'context': context,
                            'fields': ['name', 'login'],
                            'limit': 1
                        }
                    },
                    'id': 2
                }

                response = session.post(rpc_url, json=search_rpc_data)
                print(f"Search_read响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('result'):
                        user_data = result['result'][0]
                        print(f"✅ Search_read成功: {user_data}")
                    else:
                        print(f"❌ Search_read失败: {result.get('error', 'Unknown error')}")
                        error_detail = result.get('error', {})
                        if isinstance(error_detail, dict):
                            print(f"错误详情: {error_detail.get('data', {})}")
                else:
                    print(f"❌ Search_read请求失败: {response.status_code}")
                    print(f"响应内容: {response.text}")

                # 4. 测试create方法
                print("\n4️⃣ 测试create方法...")
                create_rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': 'res.partner',
                        'method': 'create',
                        'args': [{
                            'name': '调试客户',
                            'is_company': False,
                            'customer_rank': 1,
                            'email': 'debug@example.com'
                        }],
                        'kwargs': {
                            'context': context
                        }
                    },
                    'id': 3
                }

                response = session.post(rpc_url, json=create_rpc_data)
                print(f"Create响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if result.get('result'):
                        customer_id = result['result']
                        print(f"✅ Create成功: Customer ID {customer_id}")
                    else:
                        print(f"❌ Create失败: {result.get('error', 'Unknown error')}")
                        error_detail = result.get('error', {})
                        if isinstance(error_detail, dict):
                            print(f"错误详情: {error_detail.get('data', {})}")
                else:
                    print(f"❌ Create请求失败: {response.status_code}")
                    print(f"响应内容: {response.text}")

            else:
                print(f"❌ 认证失败: {result}")
        else:
            print(f"❌ 认证请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")

    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_enhanced_connection()