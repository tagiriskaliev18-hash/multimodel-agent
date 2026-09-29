import os
import json
import httpx
from typing import AsyncIterator, Dict, Any, List, Optional
from server.app.adapters.base import BaseChatAdapter
from server.app.normalizer import HermesStreamNormalizer
from server.app import config

class HermesAdapter(BaseChatAdapter):
    """
    Nous Hermes Adapter:
    - Supports OpenRouter (Hermes 3 70B/405B), Ollama (hermes3, openhermes), and free Pollinations fallback
    - Translates OpenAI tool schemas into Hermes ChatML <tools> system format
    - Normalizes streaming output into delta.reasoning (<scratchpad>/<thinking>) and delta.tool_calls (<tool_call>)
    """
    def __init__(self, backend: str = "auto", api_key: str = None, base_url: str = None):
        self.backend = backend  # "openrouter", "ollama", "pollinations", or "auto"
        self.api_key = api_key
        self.base_url = base_url

    def _resolve_backend(self, model_config: Dict[str, Any]):
        backend = model_config.get("backend", self.backend)
        if backend == "auto":
            openrouter_key = self.api_key or os.environ.get("OPENROUTER_API_KEY", "")
            if openrouter_key:
                return "openrouter", config.OPENROUTER_BASE_URL, openrouter_key
            # Check if local Ollama URL is configured
            ollama_url = model_config.get("base_url") or os.environ.get("OLLAMA_BASE_URL", config.OLLAMA_BASE_URL)
            return "ollama", ollama_url, ""
        elif backend == "openrouter":
            key = self.api_key or os.environ.get("OPENROUTER_API_KEY", "")
            url = self.base_url or config.OPENROUTER_BASE_URL
            return "openrouter", url, key
        elif backend == "ollama":
            url = self.base_url or model_config.get("base_url") or os.environ.get("OLLAMA_BASE_URL", config.OLLAMA_BASE_URL)
            return "ollama", url, ""
        elif backend == "pollinations":
            url = self.base_url or config.POLLINATIONS_BASE_URL
            return "pollinations", url, ""
        return "openrouter", config.OPENROUTER_BASE_URL, self.api_key or os.environ.get("OPENROUTER_API_KEY", "")

    def _prepare_hermes_messages(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Injects tool definitions and Hermes ChatML instructions into system message if tools are present.
        """
        if not tools:
            return messages

        tools_prompt = (
            "\n\nYou have access to the following tools. To call a tool, respond with a JSON object inside <tool_call> tags:\n"
            "<tool_call>\n"
            "{\"name\": \"function_name\", \"arguments\": {\"arg\": \"val\"}}\n"
            "</tool_call>\n\n"
            f"<tools>\n{json.dumps(tools, ensure_ascii=False, indent=2)}\n</tools>\n"
            "If you need to think through your steps before acting, use <scratchpad>...</scratchpad>."
        )

        prepared = []
        has_system = False
        for msg in messages:
            if msg.get("role") == "system":
                prepared.append({
                    "role": "system",
                    "content": msg.get("content", "") + tools_prompt
                })
                has_system = True
            else:
                prepared.append(msg)

        if not has_system:
            prepared.insert(0, {
                "role": "system",
                "content": "You are a helpful AI assistant powered by Nous Hermes." + tools_prompt
            })

        return prepared

    async def stream(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> AsyncIterator[Dict[str, Any]]:
        backend, base_url, api_key = self._resolve_backend(model_config)
        target_model = model_config.get("model", "nousresearch/hermes-3-llama-3.1-70b")
        tools = kwargs.get("tools")

        prepared_messages = self._prepare_hermes_messages(messages, tools)

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if backend == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/tagiriskaliev18-hash/multimodel-agent"
            headers["X-Title"] = "AI Duo Gateway"

        payload = {
            "model": target_model,
            "messages": prepared_messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7)
        }

        # If backend supports native tools (e.g. OpenRouter standard forwarding), include them too
        if tools and backend == "openrouter":
            payload["tools"] = tools

        normalizer = HermesStreamNormalizer(model_name=target_model)
        url = f"{base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    # If OpenRouter unauthorized (e.g. no key or invalid), automatically fallback to Pollinations/Ollama
                    if response.status_code in (401, 403) and backend == "openrouter":
                        yield {
                            "choices": [{
                                "index": 0,
                                "delta": {"reasoning": "[AI DUO Fallback]: OpenRouter ключ не обнаружен или истёк. Переключение на резервный шлюз..."},
                                "finish_reason": None
                            }],
                            "model": target_model
                        }
                        # Fallback to Pollinations
                        fallback_payload = {
                            "model": "openai",
                            "messages": prepared_messages,
                            "stream": True
                        }
                        fallback_url = f"{config.POLLINATIONS_BASE_URL}/chat/completions"
                        async with client.stream("POST", fallback_url, json=fallback_payload) as fb_resp:
                            async for fb_line in fb_resp.aiter_lines():
                                fb_line = fb_line.strip()
                                if fb_line.startswith("data: "):
                                    d_str = fb_line[6:].strip()
                                    if d_str == "[DONE]":
                                        break
                                    try:
                                        raw_chunk = json.loads(d_str)
                                        delta_txt = raw_chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        for norm_chunk in normalizer.process_delta(delta_txt):
                                            yield norm_chunk
                                    except Exception:
                                        continue
                        for rem in normalizer.finalize():
                            yield rem
                        return

                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield {
                            "choices": [{
                                "index": 0,
                                "delta": {"content": f"[Hermes/OpenRouter HTTP {response.status_code}]: {err_text.decode('utf-8', errors='replace')}"},
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
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            
                            # If chunk already has tool_calls or reasoning, pass it through directly
                            if "tool_calls" in delta or "reasoning" in delta:
                                yield chunk
                            elif content:
                                for norm_chunk in normalizer.process_delta(content):
                                    yield norm_chunk
                            else:
                                yield chunk
                        except Exception:
                            continue

                for final_chunk in normalizer.finalize():
                    yield final_chunk

            except Exception as e:
                # Connection error to primary backend (e.g. Ollama offline), fallback to free pollinations
                try:
                    fallback_payload = {
                        "model": "openai",
                        "messages": prepared_messages,
                        "stream": True
                    }
                    fallback_url = f"{config.POLLINATIONS_BASE_URL}/chat/completions"
                    async with client.stream("POST", fallback_url, json=fallback_payload) as fb_resp:
                        async for fb_line in fb_resp.aiter_lines():
                            fb_line = fb_line.strip()
                            if fb_line.startswith("data: "):
                                d_str = fb_line[6:].strip()
                                if d_str == "[DONE]":
                                    break
                                try:
                                    raw_chunk = json.loads(d_str)
                                    delta_txt = raw_chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    for norm_chunk in normalizer.process_delta(delta_txt):
                                        yield norm_chunk
                                except Exception:
                                    continue
                    for rem in normalizer.finalize():
                        yield rem
                except Exception as fb_err:
                    yield {
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"[Hermes Connection Error]: {str(e)} (Fallback error: {str(fb_err)})"},
                            "finish_reason": "error"
                        }],
                        "model": target_model
                    }

    async def complete(self, messages: List[Dict[str, Any]], model_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Collects streaming output into single completion dict"""
        accumulated_content = ""
        accumulated_reasoning = ""
        tool_calls = []

        async for chunk in self.stream(messages, model_config, **kwargs):
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                if "content" in delta and delta["content"]:
                    accumulated_content += delta["content"]
                if "reasoning" in delta and delta["reasoning"]:
                    accumulated_reasoning += delta["reasoning"]
                if "tool_calls" in delta and delta["tool_calls"]:
                    tool_calls.extend(delta["tool_calls"])

        res_msg = {"role": "assistant"}
        if accumulated_content:
            res_msg["content"] = accumulated_content
        if accumulated_reasoning:
            res_msg["reasoning"] = accumulated_reasoning
        if tool_calls:
            res_msg["tool_calls"] = tool_calls

        return {
            "choices": [{
                "message": res_msg,
                "finish_reason": "stop"
            }],
            "model": model_config.get("model", "hermes-3")
        }
