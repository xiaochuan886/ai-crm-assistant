# -*- coding: utf-8 -*-
"""
支持自动回退机制的AI Agent
优先使用LLM API，失败时自动回退到Mock服务
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
from .agent import AiAgent, ConversationContext
from .ai_services.mock_ai_service import MockAIService

logger = logging.getLogger(__name__)


class FallbackAiAgent(AiAgent):
    """支持自动回退机制的AI Agent"""

    def __init__(self, crm_adapter, ai_config: Dict[str, Any]):
        """
        初始化支持回退的AI Agent

        Args:
            crm_adapter: CRM适配器实例
            ai_config: AI配置字典，包含主要和回退配置
        """
        super().__init__(crm_adapter, ai_config)
        self.crm_adapter = crm_adapter
        self.primary_ai_config = ai_config.copy()
        self.fallback_config = ai_config.get('fallback', {})
        self.consecutive_failures = 0
        self.max_failures = self.fallback_config.get('retry_after_failures', 3)
        self.fallback_enabled = self.fallback_config.get('enable_on_failure', True)

        # 初始化主要AI服务
        try:
            # super().__init__(crm_adapter, self.primary_ai_config)
            self.using_fallback = False
            logger.info(f"AI Agent初始化成功，主要服务: {self.primary_ai_config.get('provider')}")
        except Exception as e:
            logger.error(f"主要AI服务初始化失败: {str(e)}")
            if self.fallback_enabled:
                self._init_fallback_service()
            else:
                raise

    def _init_fallback_service(self):
        """初始化回退服务"""
        try:
            fallback_config = {
                'provider': 'mock',
                'model': 'mock-model',
                'api_key': 'mock-api-key',
                'temperature': 0.1,
                'max_tokens': 500
            }

            self.ai_service = MockAIService(fallback_config)
            self.using_fallback = True
            logger.warning("已切换到Mock AI服务作为回退")
        except Exception as e:
            logger.error(f"回退服务初始化失败: {str(e)}")
            raise

    def _check_and_handle_failure(self, error: Exception) -> bool:
        """
        检查并处理AI服务失败

        Args:
            error: 发生的错误

        Returns:
            bool: 是否已切换到回退服务
        """
        self.consecutive_failures += 1
        logger.warning(f"AI服务调用失败 ({self.consecutive_failures}/{self.max_failures}): {str(error)}")

        # 如果达到最大失败次数且启用回退
        if self.consecutive_failures >= self.max_failures and self.fallback_enabled and not self.using_fallback:
            logger.info("达到最大失败次数，切换到回退服务")
            self._init_fallback_service()
            return True

        return False

    def _reset_failure_count(self):
        """重置失败计数器"""
        if self.consecutive_failures > 0:
            self.consecutive_failures = 0
            logger.debug("AI服务调用成功，重置失败计数器")

    async def _parse_intent_with_fallback(self, prompt: str) -> Dict[str, Any]:
        """
        带回退机制的意图解析

        Args:
            prompt: 输入提示

        Returns:
            意图解析结果
        """
        try:
            # 尝试使用当前AI服务
            result = await self.ai_service.parse_intent(prompt)
            self._reset_failure_count()

            # 如果使用回退服务，尝试恢复主要服务
            if self.using_fallback and self.consecutive_failures == 0:
                logger.info("尝试恢复主要AI服务")
                try:
                    super().__init__(self.crm_adapter, self.primary_ai_config)
                    self.using_fallback = False
                    logger.info("已恢复主要AI服务")
                except Exception as e:
                    logger.warning(f"主要服务恢复失败，继续使用回退服务: {str(e)}")

            return self._robust_parse_intent_result(result, prompt)

        except Exception as e:
            # 处理失败
            if self._check_and_handle_failure(e):
                # 已切换到回退服务，重试
                try:
                    result = await self.ai_service.parse_intent(prompt)
                    self._reset_failure_count()
                    return self._robust_parse_intent_result(result, prompt)
                except Exception as retry_error:
                    logger.error(f"回退服务也失败: {str(retry_error)}")

            # 返回默认结果
            return {
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.0,
                "raw_input": prompt,
                "error": str(e)
            }

    def _robust_parse_intent_result(self, result: Any, prompt: str) -> Dict[str, Any]:
        """在LLM返回空或非JSON时，健壮地解析意图，必要时使用规则回退。"""
        try:
            if result is None:
                raise ValueError("Empty intent result")

            if isinstance(result, dict):
                return result

            text = str(result).strip()
            if not text:
                raise ValueError("Blank intent result")

            # 直接尝试JSON解析
            try:
                return json.loads(text)
            except Exception:
                pass

            # 尝试从文本中提取JSON片段
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass

            # 规则回退：中文常见命令解析
            return self._rule_based_intent(prompt)

        except Exception:
            # 最终回退
            return self._rule_based_intent(prompt)

    def _rule_based_intent(self, prompt: str) -> Dict[str, Any]:
        """简单规则解析中文CRM常见意图，用于LLM异常时的兜底。"""
        p = prompt.strip()
        lower = p.lower()

        # 创建客户
        if ("创建客户" in p) or ("create" in lower and "customer" in lower):
            name = self._extract_name_after_keyword(p, ["创建客户", "客户", "customer"])
            email = self._extract_email(p)
            phone = self._extract_phone(p)
            return {
                "action": "create",
                "entity_type": "customer",
                "parameters": {k: v for k, v in {
                    "name": name,
                    "email": email,
                    "phone": phone
                }.items() if v},
                "confidence": 0.6
            }

        # 查询/搜索客户
        if ("查询客户" in p) or ("搜索客户" in p) or ("查找客户" in p) or ("search" in lower and "customer" in lower):
            name = self._extract_name_after_keyword(p, ["查询客户", "搜索客户", "查找客户", "客户", "customer"])
            return {
                "action": "search",
                "entity_type": "customer",
                "parameters": {k: v for k, v in {"name": name}.items() if v},
                "confidence": 0.6
            }

        # 默认未知
        return {
            "action": "unknown",
            "entity_type": "unknown",
            "parameters": {},
            "confidence": 0.0
        }

    def _extract_email(self, text: str) -> Optional[str]:
        m = re.search(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", text)
        return m.group(0) if m else None

    def _extract_phone(self, text: str) -> Optional[str]:
        m = re.search(r"1[3-9]\d{9}", text)  # 中国手机号简单规则
        return m.group(0) if m else None

    def _extract_name_after_keyword(self, text: str, keywords: list) -> Optional[str]:
        for kw in keywords:
            idx = text.find(kw)
            if idx != -1:
                # 提取关键词后的连续中文/字母数字作为姓名
                after = text[idx + len(kw):].strip()
                m = re.match(r"[\u4e00-\u9fa5A-Za-z0-9_]+", after)
                if m:
                    return m.group(0)
        return None

    def get_or_create_context(self, session_id: str, user_id: str):
        """Get or create conversation context"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                history=[]
            )
        return self.contexts[session_id]

    def update_context(self, context: ConversationContext, user_input: str, intent: Dict, result: Dict):
        """Update conversation context"""
        # 添加到历史记录
        context.history.append({
            "user_input": user_input,
            "intent": intent,
            "result": result,
            "timestamp": str(datetime.now())
        })

        # 限制历史记录长度
        max_rounds = getattr(self, 'conversation_max_rounds', 10)
        if len(context.history) > max_rounds:
            context.history = context.history[-max_rounds:]

    async def process_request(self, user_input: str, session_id: str = "default", user_id: str = "default") -> Dict[str, Any]:
        """
        处理用户请求，带回退机制

        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            处理结果
        """
        try:
            # 使用回退机制的意图解析
            intent_result = await self._parse_intent_with_fallback(user_input)

            # 获取或创建会话上下文
            context = self.get_or_create_context(session_id, user_id)

            # 执行意图 - 使用基类的方法
            execution_result = await self._execute_intent(intent_result, context)

            # 生成响应（也带回退机制）
            try:
                response_text = await self.ai_service.generate_response(
                    f"用户输入: {user_input}\n操作结果: {execution_result.get('message', '操作完成')}",
                    {"intent": intent_result, "result": execution_result}
                )
            except Exception as e:
                if self._check_and_handle_failure(e):
                    # 尝试用回退服务生成响应
                    response_text = await self.ai_service.generate_response(
                        f"用户输入: {user_input}\n操作结果: {execution_result.get('message', '操作完成')}",
                        {"intent": intent_result, "result": execution_result}
                    )
                else:
                    response_text = execution_result.get('message', '操作处理完成')

            # 更新会话上下文
            self.update_context(context, user_input, intent_result, execution_result)

            return {
                "session_id": session_id,
                "message": response_text,
                "intent": intent_result,
                "result": execution_result,
                "using_fallback": self.using_fallback,
                "consecutive_failures": self.consecutive_failures
            }

        except Exception as e:
            logger.error(f"请求处理失败: {str(e)}")
            return {
                "session_id": session_id,
                "message": "抱歉，处理您的请求时遇到了问题。",
                "error": str(e),
                "using_fallback": True,
                "consecutive_failures": self.consecutive_failures
            }

    def get_service_status(self) -> Dict[str, Any]:
        """获取AI服务状态"""
        return {
            "primary_provider": self.primary_ai_config.get('provider'),
            "current_provider": "mock" if self.using_fallback else self.primary_ai_config.get('provider'),
            "using_fallback": self.using_fallback,
            "consecutive_failures": self.consecutive_failures,
            "max_failures": self.max_failures,
            "fallback_enabled": self.fallback_enabled
        }