import os
import json
from typing import Dict, Any, Tuple
from server.app import config
from server.app.adapters.openai_adapter import OpenAIAdapter
from server.app.adapters.hermes_adapter import HermesAdapter
from server.app.adapters.fallback_adapter import OpenAICompatibleAdapter
from server.app.adapters.base import BaseChatAdapter

class ModelRegistry:
    def __init__(self):
        self.openai_adapter = OpenAIAdapter()
        self.hermes_adapter = HermesAdapter()
        self.generic_adapter = OpenAICompatibleAdapter()
        self._load_configurations()

    def _load_configurations(self):
        self.models: Dict[str, Dict[str, Any]] = {
            # OpenAI Models
            "gpt-4o": {
                "name": "GPT-4o",
                "adapter_type": "openai",
                "model": "gpt-4o",
                "provider": "openai",
                "description": "Флагманская мультимодальная модель OpenAI (высокая скорость и точность)",
                "tier": "premium"
            },
            "gpt-4o-mini": {
                "name": "GPT-4o-mini",
                "adapter_type": "openai",
                "model": "gpt-4o-mini",
                "provider": "openai",
                "description": "Экономичная и быстрая модель OpenAI для повседневных задач",
                "tier": "standard"
            },
            "o1": {
                "name": "OpenAI o1",
                "adapter_type": "openai",
                "model": "o1",
                "provider": "openai",
                "description": "Модель углубленного рассуждения OpenAI для сложных инженерных задач",
                "tier": "premium"
            },
            "o3-mini": {
                "name": "OpenAI o3-mini",
                "adapter_type": "openai",
                "model": "o3-mini",
                "provider": "openai",
                "description": "Компактная reasoning модель OpenAI",
                "tier": "standard"
            },

            # Nous Hermes Models
            "hermes-3": {
                "name": "Nous Hermes 3 (70B)",
                "adapter_type": "hermes",
                "model": "nousresearch/hermes-3-llama-3.1-70b",
                "provider": "hermes",
                "backend": "auto",
                "description": "Nous Hermes 3 — ведущая открытая агентная модель с поддержкой ChatML, reasoning (<scratchpad>) и tool calling (<tool_call>)",
                "tier": "free/flexible"
            },
            "hermes-405b": {
                "name": "Nous Hermes 3 (405B Free)",
                "adapter_type": "hermes",
                "model": "nousresearch/hermes-3-llama-3.1-405b:free",
                "provider": "hermes",
                "backend": "openrouter",
                "description": "Гигантская модель Hermes 3 405B через OpenRouter Free",
                "tier": "free"
            },
            "openhermes": {
                "name": "OpenHermes 2.5",
                "adapter_type": "hermes",
                "model": "openhermes",
                "provider": "hermes",
                "backend": "ollama",
                "description": "Легковесный Nous OpenHermes для локального или удаленного инференса",
                "tier": "free"
            },
            "hermes3-local": {
                "name": "Hermes 3 (Local Ollama)",
                "adapter_type": "hermes",
                "model": "hermes3",
                "provider": "hermes",
                "backend": "ollama",
                "description": "Локальный офлайн инференс Nous Hermes 3 в Ollama",
                "tier": "free"
            },

            # Free & Fast Alternatives
            "llama-3.3-70b": {
                "name": "Llama 3.3 70B (Groq)",
                "adapter_type": "generic",
                "model": "llama-3.3-70b-versatile",
                "provider": "groq",
                "base_url": config.GROQ_BASE_URL,
                "api_key_env": "GROQ_API_KEY",
                "description": "Сверхбыстрый бесплатный инференс Groq Llama 3.3 (до 300 токенов/сек)",
                "tier": "free"
            },
            "openai-fast": {
                "name": "Pollinations AI (Free Gateway)",
                "adapter_type": "generic",
                "model": "openai-fast",
                "provider": "pollinations",
                "base_url": config.POLLINATIONS_BASE_URL,
                "description": "Открытый шлюз без API ключей (публичный fallback)",
                "tier": "free"
            }
        }

    def resolve(self, requested_model: str) -> Tuple[BaseChatAdapter, Dict[str, Any]]:
        """
        Resolves model name or alias to (adapter, model_config).
        If model is unknown or empty, resolves to default model.
        """
        req_clean = (requested_model or "").strip().lower()
        if not req_clean or req_clean in ("default", "auto"):
            req_clean = config.DEFAULT_MODEL.lower()

        # Match direct or alias
        if req_clean in self.models:
            cfg = self.models[req_clean]
        elif "hermes" in req_clean:
            cfg = self.models["hermes-3"]
        elif "4o-mini" in req_clean or "gpt-4o-mini" in req_clean:
            cfg = self.models["gpt-4o-mini"]
        elif "4o" in req_clean or "gpt-4" in req_clean:
            cfg = self.models["gpt-4o"]
        elif "o1" in req_clean:
            cfg = self.models["o1"]
        elif "groq" in req_clean or "llama" in req_clean:
            cfg = self.models["llama-3.3-70b"]
        else:
            # Fallback to configured model or openai-fast
            cfg = {
                "name": requested_model,
                "adapter_type": "generic",
                "model": requested_model,
                "provider": "custom",
                "base_url": config.POLLINATIONS_BASE_URL,
                "description": "Пользовательская или внешняя модель"
            }

        atype = cfg.get("adapter_type")
        if atype == "openai":
            # If no OpenAI key is set and it's requested, check if we should fall back to Pollinations or Hermes
            return self.openai_adapter, cfg
        elif atype == "hermes":
            return self.hermes_adapter, cfg
        else:
            return self.generic_adapter, cfg

    def list_models(self) -> Dict[str, Any]:
        """Returns OpenAI-compatible /v1/models response"""
        data = []
        for mid, mcfg in self.models.items():
            data.append({
                "id": mid,
                "object": "model",
                "created": 1710000000,
                "owned_by": mcfg.get("provider", "aiduo"),
                "name": mcfg.get("name", mid),
                "description": mcfg.get("description", ""),
                "tier": mcfg.get("tier", "standard")
            })
        return {"object": "list", "data": data}

    def get_providers_status(self) -> Dict[str, Any]:
        """Returns health & connectivity summary of all providers"""
        has_openai = bool(config.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY"))
        has_openrouter = bool(config.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY"))
        has_groq = bool(config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY"))

        return {
            "openai": {
                "status": "configured" if has_openai else "needs_key",
                "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
                "description": "Native OpenAI API"
            },
            "hermes": {
                "status": "ready" if (has_openrouter or config.OLLAMA_BASE_URL) else "fallback_active",
                "backend": "openrouter" if has_openrouter else "ollama/pollinations",
                "models": ["hermes-3", "hermes-405b", "openhermes", "hermes3-local"],
                "features": ["ChatML", "reasoning (<scratchpad>)", "function calling (<tool_call>)"]
            },
            "groq": {
                "status": "configured" if has_groq else "needs_key",
                "models": ["llama-3.3-70b-versatile"]
            },
            "pollinations": {
                "status": "always_ready",
                "description": "Zero-config public gateway"
            },
            "ollama": {
                "endpoint": config.OLLAMA_BASE_URL,
                "status": "ready"
            }
        }

registry = ModelRegistry()
