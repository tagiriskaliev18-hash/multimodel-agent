# Global AI Duo & Multi-Model Architecture (powered by Claude, Agents Base & Free LLM APIs)

У тебя подключены глобальные MCP-серверы:
- `claude-bridge` (`claude_review`, `claude_ask`, `claude_implement`, `agent_run`, `agents_list`, `skills_list`, `model_ask`, `models_list`, `soup_recipe`), связывающий тебя с Claude Code, базой агентов, Free LLM API (Pollinations, Groq, OpenRouter), локальными моделями (Ollama / GGUF) и каталогом LLM Soup.
- `soup` (`advise`, `recipes_search`, `diagnose_evidence`, `ship_evidence`, `profile` и др.), предоставляющий инструменты LLMOps от Alpamys Makazhan.

Правила взаимодействия:
0. **Создание проектов (Обязательный Консилиум)**: при любых запросах на создание проектов, выбор архитектуры или стека технологий обязательно подключай Claude через `claude_ask` или агента `architect`, проводи сопоставление подходов и формируй единое рациональное решение.
1. `claude_review`: автоматически вызывай для проверки сложных изменений (>1 файла или >30 строк). Исправляй найденные критические проблемы.
2. `agent_run`: используй для делегирования специализированных задач конкретным агентам (`architect`, `reviewer`, `developer`, `security_auditor`, `llmops`) с подключением скиллов из каталога (`code-review`, `security-audit`, `architecture-audit`, `boilerplate-gen`, `llmops-tuning`).
3. `model_ask`: вызывай при сложных вопросах по архитектуре или для получения альтернативного мнения от моделей из `providers.json`.
4. Для рутинных/черновых задач и бойлерплейта прибегай к Free LLM API (`groq`, `openrouter_free`, `pollinations`), экономя квоты Claude для ключевой архитектуры и безопасности.
5. Фиксируй контрольные точки через git commit перед масштабными изменениями.
