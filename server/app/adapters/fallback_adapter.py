import os
import json
import httpx
from typing import AsyncIterator, Dict, Any, List
from server.app.adapters.base import BaseChatAdapter
from server.app import config

class OpenAICompatibleAdapter(BaseChatAdapter):
    """
    Generic OpenAI-compatible adapter for Groq, Pollinations, Ollama, DeepSeek, etc.
    """
    def __init__(self, default_base_url: str = None, default_api_key: str = None):
        self.default_base_url = default_base_url
        self.default_api_key = default_api_key

    async def stream(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        base_url = (model_config.get("base_url") or self.default_base_url or config.POLLINATIONS_BASE_URL).rstrip("/")
        api_key = model_config.get("api_key") or self.default_api_key
        if not api_key and "api_key_env" in model_config:
            api_key = os.environ.get(model_config["api_key_env"], "")

        url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        target_model = model_config.get("model", "openai-fast")
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7)
        }
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield {
                            "choices": [{
                                "index": 0,
                                "delta": {"content": f"[{model_config.get('name', 'Provider')} HTTP {response.status_code}]: {err_text.decode('utf-8', errors='replace')}"},
                                "finish_reason": "error"
                            }],
                            "model": target_model
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
                        "delta": {"content": f"[{model_config.get('name', 'Provider')} Connection Error]: {str(e)}"},
                        "finish_reason": "error"
                    }],
                    "model": target_model
                }

    async def complete(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        base_url = (model_config.get("base_url") or self.default_base_url or config.POLLINATIONS_BASE_URL).rstrip("/")
        api_key = model_config.get("api_key") or self.default_api_key
        if not api_key and "api_key_env" in model_config:
            api_key = os.environ.get(model_config["api_key_env"], "")

        url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        target_model = model_config.get("model", "openai-fast")
        payload = {
            "model": target_model,
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
                    "message": {"role": "assistant", "content": f"[{model_config.get('name', 'Provider')} HTTP {resp.status_code}]: {resp.text}"},
                    "finish_reason": "error"
                }]
            }
