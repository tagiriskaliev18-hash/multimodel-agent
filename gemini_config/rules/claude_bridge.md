---
trigger: always_on
---

# Global Claude Bridge Integration Rule

У тебя есть инструменты `claude-bridge` (`claude_review`, `claude_ask`, `claude_implement`).
Используй их автономно для перекрёстной проверки и архитектурных консультаций с Claude Code.
При `CLAUDE_LIMIT_REACHED` продолжай работу автономно.

Для больших задач: `agent_run(agent="planner")` для спецификации и плана, `agents_parallel` для независимых задач `[P]`,
`agent_pipeline` для цепочки planner → developer → reviewer. Перед работой с незнакомым кодом вызывай `repo_map`.
