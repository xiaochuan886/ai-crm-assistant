# -*- coding: utf-8 -*-
"""
Prompt Manager

This module provides a centralized way to manage and access prompt templates.
"""

import os
from typing import Dict

class PromptManager:
    """Manages loading and accessing prompt templates."""

    def __init__(self, prompt_dir: str):
        """
        Initializes the PromptManager.

        Args:
            prompt_dir: The directory where prompt templates are stored.
        """
        self.prompt_dir = prompt_dir
        self._cache: Dict[str, str] = {}

    def get_prompt(self, prompt_name: str) -> str:
        """
        Retrieves a prompt template by name.

        Args:
            prompt_name: The name of the prompt template (without extension).

        Returns:
            The content of the prompt template.

        Raises:
            FileNotFoundError: If the prompt template is not found.
        """
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        file_path = os.path.join(self.prompt_dir, f"{prompt_name}.txt")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template '{prompt_name}.txt' not found in {self.prompt_dir}")

        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        self._cache[prompt_name] = prompt_content
        return prompt_content