import os
import json
import httpx
from typing import AsyncIterator, Dict, Any, List
from server.app.adapters.base import BaseChatAdapter
from server.app import config

class OpenAIAdapter(BaseChatAdapter):
    """
    Native OpenAI API Adapter supporting GPT-4o, GPT-4o-mini, o1, etc.
    """
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.base_url = (base_url or config.OPENAI_BASE_URL).rstrip("/")

    async def stream(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            yield {
                "choices": [{
                    "index": 0,
                    "delta": {"content": "[AI DUO ERROR]: OPENAI_API_KEY не задан в переменных окружения или .env. Укажите ключ для использования моделей OpenAI."},
                    "finish_reason": "error"
                }],
                "model": model_config.get("model", "gpt-4o-mini")
            }
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_config.get("model", "gpt-4o-mini"),
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7)
        }
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs and kwargs["tool_choice"]:
            payload["tool_choice"] = kwargs["tool_choice"]
        if "max_tokens" in kwargs and kwargs["max_tokens"]:
            payload["max_tokens"] = kwargs["max_tokens"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield {
                            "choices": [{
                                "index": 0,
                                "delta": {"content": f"[OpenAI HTTP {response.status_code}]: {err_text.decode('utf-8', errors='replace')}"},
                                "finish_reason": "error"
                            }],
                            "model": payload["model"]
                        }
                        return

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            yield chunk
                        except Exception:
                            continue
            except Exception as e:
                yield {
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"[OpenAI Connection Error]: {str(e)}"},
                        "finish_reason": "error"
                    }],
                    "model": payload["model"]
                }

    async def complete(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return {
                "choices": [{
                    "message": {"role": "assistant", "content": "[AI DUO ERROR]: OPENAI_API_KEY не задан."},
                    "finish_reason": "error"
                }]
            }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_config.get("model", "gpt-4o-mini"),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7)
        }
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return resp.json()
            return {
                "choices": [{
                    "message": {"role": "assistant", "content": f"[OpenAI HTTP {resp.status_code}]: {resp.text}"},
                    "finish_reason": "error"
                }]
            }
