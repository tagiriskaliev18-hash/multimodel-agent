# ⚡ AI Duo & Multi-Model Agent Platform

> Универсальная автономная мультимодельная среда и шлюз, адаптивный к **Nous Hermes** (Hermes 3, ChatML, Reasoning `<scratchpad>`, Tool Calling `<tool_call>`), **OpenAI** (GPT-4o, GPT-4o-mini, o1), **Groq LPU**, **Ollama** и **Pollinations**.

---

## 🌟 Возможности

- **Адаптивность к Nous Hermes**:
  - Нативная поддержка спецификации Nous Hermes (ChatML, структурированные рассуждения `<scratchpad>` / `<thinking>`, вызов инструментов `<tool_call>`).
  - Потоковый парсинг и нормализация SSE-чанков в единый стандарт `delta.reasoning` и `delta.tool_calls`.
  - Поддержка различных бэкендов: OpenRouter (Hermes 3 70B/405B), локальный Ollama (`hermes3`, `openhermes`) или свободный шлюз Pollinations.
- **Адаптивность к OpenAI**:
  - Прямая интеграция с `https://api.openai.com/v1` для флагманских моделей: **GPT-4o**, **GPT-4o-mini**, **o1**, **o3-mini**.
  - Полная поддержка стриминга (Server-Sent Events) и функциональных вызовов.
- **Интеллектуальная маршрутизация и Fallback**:
  - Автоматическое переключение на резервные шлюзы при исчерпании квот или отсутствии ключей.
  - Нулевая конфигурация "из коробки" благодаря свободному открытому шлюзу Pollinations и локальным моделям Ollama.
- **Готовый Docker-образ**:
  - Легковесный multi-stage образ на базе `python:3.12-slim`.
  - Встроенный FastAPI шлюз, раздающий Web UI (AI Studio Chat, 3D Neural HUD, Service Portal) и предоставляющий OpenAI-совместимый API `/v1/chat/completions`.
- **Интеграция с MCP и базой агентов**:
  - Совместимость с Claude Code, Gemini Antigravity, LLM Soup.
  - Роли: `architect`, `reviewer`, `developer`, `security_auditor`, `llmops`, `hermes_agent`, `ui_designer`.
- **Дизайн-навыки (UI Design Kit)**:
  - Агент `ui_designer` и 4 навыка в `tools/skills/`: `ui-design-system` (тёмная тёплая тема, токены, зерно, свечение, стекло), `ui-motion` (появление при скролле, split text, бегущая строка, магнитные кнопки, подсветка под курсором, 3D-наклон, скрэмбл, счётчики, scroll-driven анимации), `ui-components` (кнопки, switch, вкладки, тосты, модалки, FAQ, скелетоны с стресс-тестом) и `landing-page-template` (одностраничная витрина).
  - Чистые HTML/CSS/JS без зависимостей, поддержка `prefers-reduced-motion` и клавиатуры.
  - Живая демонстрация всех эффектов: `tools/design-kit/index.html` (в Docker по адресу `/design`).

---

## 🚀 Быстрый запуск через Docker

### 1. Запуск с помощью Docker Compose

```bash
# Клонируйте репозиторий
git clone https://github.com/tagiriskaliev18-hash/multimodel-agent.git
cd multimodel-agent

# Создайте .env файл при необходимости
cp .env.example .env

# Запустите весь стек (AI Duo Gateway + локальная Ollama)
docker compose up -d --build
```

После запуска сервисы доступны по адресам:
- **AI Studio Chat**: [http://localhost:8000/chat](http://localhost:8000/chat)
- **3D Neural HUD**: [http://localhost:8000/hud](http://localhost:8000/hud)
- **Design Kit (живая витрина дизайн-навыков)**: [http://localhost:8000/design](http://localhost:8000/design)
- **Сервисный портал**: [http://localhost:8000/](http://localhost:8000/)
- **OpenAI-совместимый API**: `http://localhost:8000/v1/chat/completions`
- **Проверка здоровья**: [http://localhost:8000/healthz](http://localhost:8000/healthz)

### 2. Сборка и запуск одного Docker-образа

```bash
# Сборка образа
docker build -t aiduo-agent:latest .

# Запуск контейнера
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY="sk-..." \
  -e OPENROUTER_API_KEY="sk-or-..." \
  -e GROQ_API_KEY="gsk_..." \
  --name aiduo \
  aiduo-agent:latest
```

---

## ⚙️ Переменные окружения (`.env`)

| Переменная | Описание | Обязательность |
|---|---|---|
| `OPENAI_API_KEY` | Ключ доступа к OpenAI (GPT-4o, GPT-4o-mini, o1) | Опционально |
| `OPENROUTER_API_KEY` | Ключ OpenRouter для Nous Hermes 3 (70B / 405B) | Опционально |
| `GROQ_API_KEY` | Бесплатный ключ Groq (Llama 3.3 70B, ~450 токенов/сек) | Опционально |
| `OLLAMA_BASE_URL` | Адрес локального инстанса Ollama (по умолч.: `http://127.0.0.1:11434/v1`) | Опционально |
| `PORT` | Порт веб-шлюза (по умолч.: `8000`) | Опционально |
| `AIDUO_DEFAULT_MODEL` | Модель по умолчанию (`gpt-4o-mini`, `hermes-3`, `openai-fast`) | Опционально |

> *Примечание: Если ни один ключ не задан, шлюз автоматически переходит в бесплатный автономный режим через Pollinations и локальную Ollama.*

---

## 🧠 Адаптер Nous Hermes

Nous Hermes обладает развитыми способностями к рассуждению и вызову функций. Встроенный адаптер (`HermesAdapter` + `HermesStreamNormalizer`):
1. **Инжектирует схемы инструментов** в системный промпт формата ChatML:
   ```xml
   <tools>
   [JSON Tool Specifications]
   </tools>
   ```
2. **Перехватывает цепочки рассуждений** `<scratchpad>...</scratchpad>` и транслирует их в стандартное поле `delta.reasoning` (для отображения скрытых мыслей модели в UI).
3. **Парсит вызовы инструментов** `<tool_call>{"name": "...", "arguments": {...}}</tool_call>` и конвертирует их в нативный формат OpenAI Function Calling `delta.tool_calls`.

---

## 🛠 Локальная разработка без Docker

```bash
# Установка зависимостей
pip install -r server/requirements.txt

# Запуск сервера разработки
uvicorn server.app.main:app --reload --port 8000
```

---

## 📂 Структура проекта

```
multimodel-agent/
├── server/                    # FastAPI шлюз и адаптеры моделей
│   ├── app/
│   │   ├── adapters/          # Адаптеры OpenAI, Hermes, Groq, Ollama
│   │   ├── normalizer.py      # Потоковый SSE-нормализатор тегов Hermes
│   │   ├── registry.py        # Реестр и роутер моделей
│   │   ├── config.py          # Конфигурация и переменные окружения
│   │   └── main.py            # Точка входа FastAPI и статические роуты
│   └── requirements.txt
├── ai-chat/                   # Клиентское приложение AI Studio Chat
├── portal/                    # Корпоративный сервисный портал
├── tools/
│   ├── hud/                   # 3D Sci-Fi Neural HUD управления моделями
│   ├── claude_bridge.py       # MCP сервер связки с Claude Code / Gemini
│   ├── providers.json         # Глобальный реестр провайдеров
│   ├── agents.json            # База агентов (architect, developer, hermes_agent...)
│   ├── design-kit/            # Живая витрина дизайн-навыков (/design)
│   └── skills/                # Каталог навыков (code-review, audit, tuning, ui-*...)
├── Dockerfile                 # Docker образ приложения
├── docker-compose.yml         # Стек с контейнером Ollama
├── .env.example               # Шаблон настроек
└── README.md
```

---

## 📄 Лицензия

MIT License © 2026 AI Duo Team.
