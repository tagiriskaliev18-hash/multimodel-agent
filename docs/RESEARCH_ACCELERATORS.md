# Ускорители кодинга с GitHub: что взяли в AI Duo и что стоит подключить

Обзор проектов (сентябрь 2026), которые реально ускоряют разработку с ИИ-агентами **без потери качества**, и как их идеи встроены в `tools/claude_bridge.py`.

## Что уже встроено в AI Duo

| Идея | Источник | Где у нас | Эффект |
|---|---|---|---|
| Карта репозитория (символы и сигнатуры вместо файлов) | [aider](https://github.com/Aider-AI/aider) repo map | `repo_map`, автоматически в `agent_run` для API-моделей | Groq/Hermes/OpenAI видят структуру проекта за ~5-10% токенов и пишут код, который вписывается в существующие модули |
| Упаковка репозитория в один контекст | [repomix](https://github.com/yamadashy/repomix) | `repo_pack` | Полный контекст выбранных файлов с учётом `.gitignore` и бюджета |
| Spec → Plan → Tasks → Implement | [github/spec-kit](https://github.com/github/spec-kit) | агент `planner`, скилл `spec-driven-development` | Меньше переделок: требования и критерии приёмки фиксируются до кода |
| План из задач по 2-5 минут с зависимостями и `[P]` | [obra/superpowers](https://github.com/obra/superpowers), [Task Master](https://github.com/eyaltoledano/claude-task-master) | скилл `writing-plans` | Независимые задачи можно раздавать параллельно |
| TDD, системная отладка, проверка перед «готово» | [obra/superpowers](https://github.com/obra/superpowers) | скиллы `test-driven-development`, `systematic-debugging`, `verification-before-completion`; агенты `tester`, `debugger` | Скорость не ценой регрессий: без доказательства «готово» не принимается |
| Конвейер агентов с передачей артефактов | [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | `agent_pipeline` (по умолчанию planner → developer → reviewer) | Одна команда проводит фичу от идеи до ревью |
| Параллельные агенты + синтез лучшего ответа | Mixture-of-Agents, `dispatching-parallel-agents` из superpowers | `agents_parallel` с опциональным `judge` | Дешёвые быстрые модели работают одновременно, сильная модель только сводит итог |

## Рекомендуем подключить как MCP-серверы (без изменения кода)

| Проект | Зачем |
|---|---|
| [oraios/serena](https://github.com/oraios/serena) | Семантический поиск и правка кода через language server: «найди все вызовы функции» вместо grep |
| [upstash/context7](https://github.com/upstash/context7) | Актуальная документация библиотек в контексте: меньше галлюцинаций про устаревшие API |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Агент сам открывает UI (чат, HUD, портал), читает консоль и сеть |
| [ast-grep](https://github.com/ast-grep/ast-grep) | Структурный поиск и массовые рефакторинги по AST |

## Каталоги для дальнейшего поиска

- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code): скиллы, хуки, команды, оркестраторы
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills): скиллы, которые используют реальные команды
- [anthropics/skills](https://github.com/anthropics/skills): официальные скиллы Anthropic
- [nhconganhmedia/awesome-engineering-ai](https://github.com/nhconganhmedia/awesome-engineering-ai): карта инструментов по категориям (контекст, память, spec-driven, параллельные агенты)

## Рекомендуемый рабочий цикл для больших проектов

1. `agent_run(agent="planner", task="<идея>")`: спецификация и план с задачами `[P]`.
2. `agents_parallel(agents=[...], task="T3", judge="reviewer")` для независимых задач или сложных решений.
3. `agent_pipeline(task="<фича>", stages=["developer", "tester", "reviewer"])` для каждой зависимой задачи.
4. `claude_implement` применяет изменения (скилл `verification-before-completion` подключается автоматически).
5. `claude_review` для финальной проверки ветки.
