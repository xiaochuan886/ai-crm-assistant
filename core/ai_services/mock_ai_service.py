# -*- coding: utf-8 -*-
"""
Mock AI Service for Testing

This module provides a mock AI service for testing and development purposes.
It simulates AI responses without making actual API calls.
"""

import json
import logging
from typing import Dict, Any
from .openai_service import BaseAiService


logger = logging.getLogger(__name__)


class MockAIService(BaseAiService):
    """Mock AI service for testing"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Mock AI service

        Args:
            config: Dictionary containing mock configuration
        """
        self.provider = config.get('provider', 'mock')
        self.model = config.get('model', 'mock-model')
        logger.info(f"初始化Mock AI服务: {self.model}")

    async def parse_intent(self, prompt: str) -> str:
        """
        Mock intent parsing using simple pattern matching

        Args:
            prompt: User input prompt

        Returns:
            JSON string with mock intent information
        """
        try:
            # 如果是复杂prompt，提取实际的用户输入部分
            user_input = self._extract_user_input_from_prompt(prompt)

            # 如果提取不到用户输入，直接使用原始prompt
            if not user_input:
                user_input = prompt

            prompt_lower = user_input.lower().strip()

            # 简单的关键词匹配
            if any(word in prompt_lower for word in ['你好', 'hello', 'hi', '嗨', '您好']):
                return json.dumps({
                    "action": "greeting",
                    "entity_type": "none",
                    "parameters": {},
                    "confidence": 1.0,
                    "raw_input": user_input
                }, ensure_ascii=False)

            elif any(word in prompt_lower for word in ['创建', '新增', '添加', '建立', 'create']):
                if any(word in prompt_lower for word in ['客户', '顾客', 'customer']):
                    return json.dumps({
                        "action": "create",
                        "entity_type": "customer",
                        "parameters": self._extract_customer_info(user_input),
                        "confidence": 0.8,
                        "raw_input": user_input
                    }, ensure_ascii=False)

            elif any(word in prompt_lower for word in ['搜索', '查找', '找', 'search', '找一下']):
                if any(word in prompt_lower for word in ['客户', '顾客', 'customer']):
                    # 提取搜索关键词
                    search_term = self._extract_search_term(user_input)
                    return json.dumps({
                        "action": "search",
                        "entity_type": "customer",
                        "parameters": {
                            "name": search_term,
                            "limit": 10
                        },
                        "confidence": 0.9,
                        "raw_input": user_input
                    }, ensure_ascii=False)

            elif any(word in prompt_lower for word in ['编辑', '修改', '更新', 'update', '改变']):
                if any(word in prompt_lower for word in ['客户', '顾客', 'customer']):
                    return json.dumps({
                        "action": "update",
                        "entity_type": "customer",
                        "parameters": self._extract_customer_info(user_input),
                        "confidence": 0.8,
                        "raw_input": user_input
                    }, ensure_ascii=False)

            # 默认响应
            return json.dumps({
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.3,
                "raw_input": user_input
            }, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Mock AI intent parsing failed: {str(e)}")
            return json.dumps({
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.1,
                "raw_input": prompt,
                "error": str(e)
            }, ensure_ascii=False)

    async def generate_response(self, prompt: str, context: Dict = None) -> str:
        """
        Generate mock natural language response

        Args:
            prompt: The prompt to respond to
            context: Optional context information

        Returns:
            Generated mock response text
        """
        try:
            prompt_lower = prompt.lower().strip()

            if any(word in prompt_lower for word in ['你好', 'hello', 'hi', '嗨', '您好']):
                return "您好！我是AI CRM助手，可以帮助您管理客户、产品和订单。请问有什么可以帮助您的吗？"

            elif '创建' in prompt_lower and '客户' in prompt_lower:
                return "客户创建成功！我已经为您添加了新的客户信息。"

            elif '搜索' in prompt_lower and '客户' in prompt_lower:
                return "我已经为您搜索了相关客户信息，请查看搜索结果。"

            elif '更新' in prompt_lower or '修改' in prompt_lower:
                return "客户信息更新成功！修改已保存。"

            elif '订单' in prompt_lower:
                return "订单操作已完成。"

            else:
                return "操作处理完成。如果您需要其他帮助，请随时告诉我。"

        except Exception as e:
            logger.error(f"Mock response generation failed: {str(e)}")
            return "抱歉，处理您的请求时遇到了问题。"

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
            return self._extract_customer_info(text)
        except Exception as e:
            logger.error(f"Mock entity extraction failed: {str(e)}")
            return {}

    def _extract_customer_info(self, text: str) -> Dict[str, Any]:
        """Extract customer information from text"""
        entities = {}

        # 简单的邮箱提取
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            entities['email'] = emails[0]

        # 简单的电话号码提取
        phone_pattern = r'\b1[3-9]\d{9}\b|\b\d{3,4}-\d{7,8}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities['phone'] = phones[0]

        # 简单的姓名提取（假设姓名在开头或包含特定关键词）
        name_patterns = [
            r'名[叫是]([^，。！？\s]{2,10})',
            r'我是([^，。！？\s]{2,10})',
            r'客户[叫是]([^，。！？\s]{2,10})',
        ]
        for pattern in name_patterns:
            names = re.findall(pattern, text)
            if names:
                entities['name'] = names[0]
                break

        # 简单的公司名称提取
        company_patterns = [
            r'公司[叫是]([^，。！？\s]{2,20})',
            r'在([^，。！？\s]{2,20})公司',
        ]
        for pattern in company_patterns:
            companies = re.findall(pattern, text)
            if companies:
                entities['company'] = companies[0]
                break

        return entities

    def _extract_search_term(self, text: str) -> str:
        """Extract search term from text"""
        # 移除搜索相关关键词，保留核心搜索词
        search_keywords = ['搜索', '查找', '找', 'search', '客户', '顾客', 'customer']
        for keyword in search_keywords:
            text = text.replace(keyword, '')

        # 清理并返回
        search_term = text.strip()
        if search_term and len(search_term) > 0:
            return search_term
        return ""

    def _extract_user_input_from_prompt(self, prompt: str) -> str:
        """Extract actual user input from complex AI prompt"""
        try:
            # 查找 "User input: " 后面的内容
            import re

            # 匹配 "User input: " 后面的内容，可能在引号内
            patterns = [
                r'User input:\s*"([^"]+)"',  # User input: "content"
                r'User input:\s*([^\n]+)',    # User input: content (直到换行)
                r'用户输入[：:]\s*"([^"]+)"',  # 中文版本
                r'用户输入[：:]\s*([^\n]+)',    # 中文版本，无引号
            ]

            for pattern in patterns:
                matches = re.findall(pattern, prompt)
                if matches:
                    user_input = matches[0].strip()
                    if user_input:
                        return user_input

            # 如果没有找到特定的模式，查找最后一行的可能用户输入
            lines = prompt.split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith('You are') and not line.startswith('Analyze') and not line.startswith('Recent'):
                    # 可能是用户输入
                    if any(word in line.lower() for word in ['创建', '新增', '客户', '你好', '搜索', '编辑', '修改']):
                        return line

            return ""

        except Exception as e:
            logger.error(f"提取用户输入失败: {e}")
            return ""