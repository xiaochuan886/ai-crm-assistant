from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAiService(ABC):
    """Base class for AI services"""

    @abstractmethod
    async def parse_intent(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Parse user intent from prompt"""
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a natural language response"""
        pass

    @abstractmethod
    async def extract_entities(self, prompt: str, intent: Dict[str, Any]) -> str:
        """Extract entities from prompt based on intent"""
        pass