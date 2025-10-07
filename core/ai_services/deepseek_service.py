# -*- coding: utf-8 -*-
"""
DeepSeek AI Service Integration for ModelScope

This module provides integration with DeepSeek models via ModelScope platform
for enhanced Chinese language processing capabilities.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from .openai_service import BaseAiService


logger = logging.getLogger(__name__)


class DeepSeekService(BaseAiService):
    """DeepSeek AI service implementation via ModelScope"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DeepSeek service

        Args:
            config: Dictionary containing:
                - auth_token: ModelScope auth token
                - base_url: ModelScope API base URL
                - model: Model name (default: deepseek-ai/DeepSeek-V3.2-Exp)
                - temperature: Sampling temperature (default: 0.1)
                - max_tokens: Maximum tokens (default: 2000)
        """
        self.auth_token = config.get('auth_token')
        self.base_url = config.get('base_url', 'https://api-inference.modelscope.cn')
        self.model = config.get('model', 'deepseek-ai/DeepSeek-V3.2-Exp')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 2000)

        # API endpoint
        self.api_url = f"{self.base_url}/v1/chat/completions"

        if not self.auth_token:
            raise ValueError("ModelScope auth token is required")

        # 验证连接
        self._validate_connection()

    def _validate_connection(self):
        """Validate ModelScope API connection"""
        try:
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }

            response = requests.post(
                self.api_url,
                json=test_payload,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                logger.info("DeepSeek API connection validated successfully")
            else:
                logger.warning(f"DeepSeek API validation failed: {response.status_code}")

        except Exception as e:
            logger.warning(f"Could not validate DeepSeek connection: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    async def parse_intent(self, prompt: str) -> str:
        """
        Parse user intent from prompt using DeepSeek

        Args:
            prompt: User input prompt

        Returns:
            JSON string with intent information
        """
        try:
            system_prompt = """你是一个专业的CRM系统AI助手。请分析用户请求并识别操作意图。

用户请求: "{user_input}"

可能的操作类型:
- create_customer: 创建客户
- search_customers: 搜索客户
- get_customer: 获取客户详情
- update_customer: 更新客户信息
- create_order: 创建订单
- search_products: 搜索产品
- create_lead: 创建销售线索

请以JSON格式返回识别结果，包含以下字段：
{
  "intent": "操作类型",
  "entities": {
    "name": "提取的姓名",
    "email": "提取的邮箱",
    "phone": "提取的电话",
    "company": "提取的公司",
    "description": "提取的描述信息"
  },
  "confidence": 0.95,
  "raw_input": "原始用户输入"
}

请只返回JSON，不要添加其他解释。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'用户请求: "{prompt}"'}
            ]

            response = self._call_api(messages)

            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']

                # 尝试解析JSON响应
                try:
                    # 清理响应内容，移除可能的代码块标记
                    clean_content = content.strip()
                    if clean_content.startswith('```json'):
                        clean_content = clean_content[7:]
                    if clean_content.endswith('```'):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()

                    # 验证JSON格式
                    parsed = json.loads(clean_content)
                    return json.dumps(parsed, ensure_ascii=False)

                except json.JSONDecodeError:
                    # 如果JSON解析失败，创建默认响应
                    logger.warning(f"Failed to parse JSON from DeepSeek response: {content}")
                    default_response = {
                        "intent": "unknown",
                        "entities": {},
                        "confidence": 0.5,
                        "raw_input": prompt
                    }
                    return json.dumps(default_response, ensure_ascii=False)

            # 如果没有有效响应，返回默认值
            default_response = {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.3,
                "raw_input": prompt
            }
            return json.dumps(default_response, ensure_ascii=False)

        except Exception as e:
            logger.error(f"DeepSeek intent parsing failed: {str(e)}")
            return json.dumps({
                "intent": "unknown",
                "entities": {},
                "confidence": 0.1,
                "raw_input": prompt,
                "error": str(e)
            }, ensure_ascii=False)

    async def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generate natural language response

        Args:
            prompt: The prompt to respond to
            context: Optional context information

        Returns:
            Generated response text
        """
        try:
            system_prompt = """你是一个专业的CRM系统AI助手。请根据用户的操作结果，生成自然、友好的中文回应。

回应原则：
1. 使用简洁、专业的中文
2. 突出操作结果和关键信息
3. 提供有用的后续建议
4. 保持友好和专业的语调

示例回应：
- "客户张三已成功创建，客户ID为123"
- "找到5个匹配的客户信息"
- "订单创建完成，总金额为¥1,500" """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = self._call_api(messages)

            if response and 'choices' in response:
                return response['choices'][0]['message']['content'].strip()

            return "操作处理完成"

        except Exception as e:
            logger.error(f"DeepSeek response generation failed: {str(e)}")
            return "抱歉，处理您的请求时遇到了问题。"

    def _call_api(self, messages: list) -> Optional[Dict]:
        """
        Make API call to DeepSeek

        Args:
            messages: List of message dictionaries

        Returns:
            API response dictionary or None
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {str(e)}")
            return None

    async def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Extract entities from text based on intent

        Args:
            text: Input text
            intent: Identified intent

        Returns:
            Dictionary of extracted entities
        """
        try:
            system_prompt = f"""请从用户输入中提取实体信息。

用户输入: "{text}"
识别意图: {intent}

请提取以下信息（如果存在）：
- name: 姓名
- email: 邮箱地址
- phone: 电话号码
- company: 公司名称
- description: 描述信息
- product_name: 产品名称
- quantity: 数量
- price: 价格

请以JSON格式返回结果。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请提取实体: {text}"}
            ]

            response = self._call_api(messages)

            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']

                try:
                    # 清理并解析JSON
                    clean_content = content.strip()
                    if clean_content.startswith('```json'):
                        clean_content = clean_content[7:]
                    if clean_content.endswith('```'):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()

                    return json.loads(clean_content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse entities JSON: {content}")

            return {}

        except Exception as e:
            logger.error(f"DeepSeek entity extraction failed: {str(e)}")
            return {}