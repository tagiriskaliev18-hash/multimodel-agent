from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, List

class BaseChatAdapter(ABC):
    @abstractmethod
    async def stream(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """Yields OpenAI-compatible chunk dicts"""
        pass

    @abstractmethod
    async def complete(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Returns standard OpenAI-compatible response dict"""
        pass
