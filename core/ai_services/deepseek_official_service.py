# -*- coding: utf-8 -*-
"""
DeepSeek Official API Service Integration

This module provides integration with DeepSeek models via official DeepSeek API
for enhanced Chinese language processing capabilities.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

from core.ai_services.base import BaseAiService
from core.prompts.prompt_manager import PromptManager


logger = logging.getLogger(__name__)


class DeepSeekOfficialService(BaseAiService):
    """DeepSeek AI service implementation"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DeepSeek AI service
        """
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'deepseek-chat')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 500)
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.prompt_manager = PromptManager(config.get('prompt_dir', 'core/prompts'))

        if not self.api_key:
            raise ValueError("DeepSeek API key is required")

    async def parse_intent(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Parse user intent using DeepSeek AI
        """
        try:
            system_prompt = self.prompt_manager.get_prompt('intent_parsing')
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            return await self._call_api(messages)

        except Exception as e:
            logger.error(f"Error in DeepSeek intent parsing: {str(e)}")
            return json.dumps({
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.0
            })

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a natural language response using DeepSeek AI
        """
        try:
            system_prompt = self.prompt_manager.get_prompt('response_generation')

            user_message = prompt
            if context:
                if isinstance(context, dict) and 'intent' in context:
                    intent_info = context['intent']
                    if isinstance(intent_info, dict):
                        user_message += f"\n\n用户意图: {intent_info.get('action', '')} {intent_info.get('entity_type', '')}"
                if 'result' in context:
                    result_info = context['result']
                    if isinstance(result_info, dict):
                        user_message += f"\n操作结果: {result_info.get('message', '')}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            return await self._call_api(messages)

        except Exception as e:
            logger.error(f"Error in DeepSeek response generation: {str(e)}")
            return "抱歉，我现在无法生成回应。请稍后再试。"

    async def extract_entities(self, prompt: str, intent: Dict[str, Any]) -> str:
        """
        Extract entities from user input based on intent
        """
        try:
            system_prompt = self.prompt_manager.get_prompt('entity_extraction')

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            return await self._call_api(messages)

        except Exception as e:
            logger.error(f"Error in DeepSeek entity extraction: {str(e)}")
            return json.dumps({})

    async def _call_api(self, messages: list) -> str:
        """
        Call DeepSeek API
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        logger.debug(f"DeepSeek API Request: {json.dumps(data, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            logger.debug(f"DeepSeek API Response Status: {response.status_code}")
            logger.debug(f"DeepSeek API Response Body: {response.text}")

            response.raise_for_status()
            result = response.json()

            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                logger.warning("DeepSeek API returned empty content.")
                return "{}"

            logger.debug(f"Extracted content: {content}")
            return content

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.text}")
            return "{}"
        except Exception as e:
            logger.error(f"An error occurred in _call_api: {e}")
            return "{}"