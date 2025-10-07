#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import requests
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_http_integration():
    """测试HTTP API集成"""

    base_url = "http://localhost:8000"

    print("🔍 测试1: 健康检查")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

    print("\n🤖 测试2: LLM意图解析（你好）")
    try:
        test_data = {
            "message": "你好",
            "session_id": "test_session_001"
        }

        response = requests.post(
            f"{base_url}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ LLM调用成功！")
                print(f"AI回复: {result.get('response', '无回复')}")
            else:
                print(f"❌ 业务处理失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")

    except Exception as e:
        print(f"❌ LLM测试失败: {e}")
        return False

    print("\n👥 测试3: 复杂客户创建意图")
    try:
        test_data = {
            "message": "创建客户 小花 13255552225 569@qq.com",
            "session_id": "test_session_002"
        }

        response = requests.post(
            f"{base_url}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 复杂意图处理成功！")
                print(f"AI回复: {result.get('response', '无回复')}")
            else:
                print(f"❌ 业务处理失败: {result.get('message', '未知错误')}")

    except Exception as e:
        print(f"❌ 复杂意图测试失败: {e}")
        return False

    print("\n✅ 集成测试完成！")
    return True

if __name__ == "__main__":
    asyncio.run(test_http_integration())