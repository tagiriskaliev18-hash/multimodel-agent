import sys
import json
import os
import subprocess
import traceback
import urllib.request
import urllib.error

import shutil
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_context  # noqa: E402

CLAUDE_PATH = os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe")
if not os.path.exists(CLAUDE_PATH):
    resolved_claude = shutil.which("claude")
    CLAUDE_PATH = resolved_claude if resolved_claude else "claude"

DEFAULT_MODEL = os.environ.get("CLAUDE_BRIDGE_MODEL", "sonnet")
REPO_MAP_BUDGET = int(os.environ.get("AIDUO_REPO_MAP_CHARS", "8000"))
PARALLEL_WORKERS = int(os.environ.get("AIDUO_PARALLEL_WORKERS", "4"))
ERROR_PREFIXES = ("CLAUDE_ERROR", "CLAUDE_LIMIT_REACHED", "PROVIDER_ERROR", "PROVIDER_OFFLINE",
                  "PROVIDER_LIMIT_REACHED", "AGENT_ERROR", "SOUP_ERROR", "BRIDGE_ERROR", "REPO_ERROR")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PROVIDERS = {
    "default_provider": "claude",
    "providers": {
        "claude": {
            "type": "cli",
            "command": "claude",
            "model": "sonnet",
            "tier": "premium",
            "privacy": "private",
            "description": "Claude Code CLI (главный архитектор, ревьюер и аудитор безопасности)"
        },
        "pollinations": {
            "type": "openai_compatible",
            "base_url": "https://text.pollinations.ai/openai",
            "model": "openai-fast",
            "tier": "free",
            "privacy": "public",
            "description": "FREE LLM API (Pollinations) — открытый шлюз без API-ключей для публичных/шаблонных задач"
        },
        "groq": {
            "type": "openai_compatible",
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile",
            "api_key_env": "GROQ_API_KEY",
            "tier": "free",
            "privacy": "private",
            "description": "Groq Free Tier — сверхбыстрый инференс Llama 3.3 70B (бесплатно)"
        },
        "openrouter_free": {
            "type": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "api_key_env": "OPENROUTER_API_KEY",
            "tier": "free",
            "privacy": "private",
            "description": "OpenRouter Free Pool — бесплатные модели :free (Llama 3.3, DeepSeek R1)"
        },
        "github_models": {
            "type": "openai_compatible",
            "base_url": "https://models.inference.ai.azure.com",
            "model": "gpt-4o-mini",
            "api_key_env": "GITHUB_TOKEN",
            "tier": "free",
            "privacy": "private",
            "description": "GitHub Models — бесплатный доступ через личный токен GitHub"
        },
        "ollama": {
            "type": "openai_compatible",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "qwen2.5-coder:1.5b",
            "api_key": "ollama",
            "tier": "free",
            "privacy": "private",
            "description": "Локальный Ollama (быстрая легковесная офлайн-модель на CPU)"
        },
        "soup_local": {
            "type": "openai_compatible",
            "base_url": "http://127.0.0.1:8080/v1",
            "model": "default",
            "api_key": "soup",
            "tier": "free",
            "privacy": "private",
            "description": "Локальный llama.cpp / Soup llama-server (офлайн)"
        },
        "deepseek": {
            "type": "openai_compatible",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-coder",
            "api_key_env": "DEEPSEEK_API_KEY",
            "tier": "premium",
            "privacy": "private",
            "description": "DeepSeek API (высокоточный код и рассуждения)"
        },
        "openai": {
            "type": "openai_compatible",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "tier": "premium",
            "privacy": "private",
            "description": "OpenAI API (GPT-4o, GPT-4o-mini, o1)"
        },
        "hermes": {
            "type": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "nousresearch/hermes-3-llama-3.1-70b",
            "api_key_env": "OPENROUTER_API_KEY",
            "tier": "free/flexible",
            "privacy": "private",
            "description": "Nous Hermes 3 (70B) — агентная модель с ChatML, reasoning (<scratchpad>) и tool calling"
        },
        "hermes_local": {
            "type": "openai_compatible",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "hermes3",
            "api_key": "ollama",
            "tier": "free",
            "privacy": "private",
            "description": "Локальный Nous Hermes 3 в Ollama"
        }
    }
}

def log(msg):
    sys.stderr.write(f"[ai-bridge] {msg}\n")
    sys.stderr.flush()

def load_providers():
    candidate_paths = [
        os.path.join(BASE_DIR, "providers.json"),
        os.path.expandvars(r"%USERPROFILE%\.aiduo\providers.json"),
        r"C:\projects\tools\providers.json"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log(f"Ошибка чтения {path}: {e}")
    return DEFAULT_PROVIDERS

def load_agents():
    candidate_paths = [
        os.path.join(BASE_DIR, "agents.json"),
        os.path.expandvars(r"%USERPROFILE%\.aiduo\agents.json"),
        r"C:\projects\tools\agents.json"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log(f"Ошибка чтения {path}: {e}")
    return {"default_agent": "developer", "agents": {}}

def load_skill(skill_name):
    if not skill_name:
        return ""
    safe_name = os.path.basename(skill_name.strip())
    filename = safe_name if safe_name.endswith(".md") else f"{safe_name}.md"
    candidate_dirs = [
        os.path.join(BASE_DIR, "skills"),
        os.path.expandvars(r"%USERPROFILE%\.aiduo\skills"),
        r"C:\projects\tools\skills"
    ]
    for sdir in candidate_dirs:
        path = os.path.join(sdir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                log(f"Ошибка чтения скилла {path}: {e}")
    return ""

def validate_work_folder(work_folder):
    if not work_folder or not os.path.isdir(work_folder):
        return False, f"CLAUDE_ERROR: Рабочая папка '{work_folder}' не найдена или не является директорией."
    return True, os.path.abspath(work_folder)

def run_claude(cwd, prompt, tools_arg=None, allow_writes=False, model=None):
    ok, validated_cwd = validate_work_folder(cwd)
    if not ok:
        return validated_cwd

    target_model = model or DEFAULT_MODEL
    base_cmd = [CLAUDE_PATH, "-p", prompt, "--model", target_model]
    if tools_arg is not None:
        base_cmd.extend(["--tools", tools_arg])
    if allow_writes:
        base_cmd.append("--dangerously-skip-permissions")
        
    cmd = base_cmd
    if sys.platform == "win32" and CLAUDE_PATH.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd.exe", "/c"] + base_cmd
    
    log(f"Running command in {validated_cwd}: {' '.join(cmd[:4])}...")
    try:
        env = os.environ.copy()
        ca_path = r"C:\projects\tools\corporate_ca.pem"
        if os.path.exists(ca_path):
            env["NODE_EXTRA_CA_CERTS"] = ca_path
            env["SSL_CERT_FILE"] = ca_path
            env["REQUESTS_CA_BUNDLE"] = ca_path
        res = subprocess.run(
            cmd,
            cwd=validated_cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=300
        )
        output = res.stdout.strip()
        stderr = res.stderr.strip()
        
        # Check for rate limit / quota
        limit_signals = [
            "rate limit",
            "usage limit",
            "exhausted your current quota",
            "hit your limit",
            "too many requests",
            "limit reached"
        ]
        combined = (output + "\n" + stderr).lower()
        for sig in limit_signals:
            if sig in combined:
                log(f"Limit signal detected: {sig}")
                return f"CLAUDE_LIMIT_REACHED: {output or stderr}"
                
        if res.returncode != 0 and not output:
            return f"CLAUDE_ERROR (code {res.returncode}): {stderr}"
            
        return output if output else (stderr if stderr else "Успешно выполнено (без текстового вывода).")
    except subprocess.TimeoutExpired:
        log("Execution timed out (300s)")
        return "CLAUDE_ERROR: Превышено время ожидания ответа от Claude (5 минут)."
    except Exception as e:
        log(f"Exception during execution: {e}")
        return f"CLAUDE_ERROR: {str(e)}"

def run_openai_compatible(config, prompt, system_prompt=None, timeout=60):
    base_url = config.get("base_url", "http://127.0.0.1:11434/v1").rstrip("/")
    url = f"{base_url}/chat/completions"
    api_key = config.get("api_key")
    if not api_key and "api_key_env" in config:
        env_var = config["api_key_env"]
        api_key = os.environ.get(env_var, "")
        if not api_key:
            return f"PROVIDER_ERROR: Переменная окружения '{env_var}' не задана для провайдера."
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": config.get("model", "default"),
        "messages": messages,
        "temperature": config.get("temperature", 0.2)
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    ssl_context = None
    ca_path = r"C:\projects\tools\corporate_ca.pem"
    if os.path.exists(ca_path):
        import ssl
        try:
            ssl_context = ssl.create_default_context(cafile=ca_path)
        except Exception:
            pass

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")
            return json.dumps(data, ensure_ascii=False, indent=2)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if e.code == 429:
            return f"PROVIDER_LIMIT_REACHED (HTTP 429 Rate Limit): {err_body}".strip()
        return f"PROVIDER_ERROR (HTTP {e.code}): {e.reason}. {err_body}".strip()
    except urllib.error.URLError as e:
        return f"PROVIDER_OFFLINE: Не удалось связаться с {url}: {e.reason}"
    except Exception as e:
        return f"PROVIDER_ERROR: {str(e)}"

def handle_review(work_folder, focus=""):
    diff_info = ""
    try:
        if os.path.exists(os.path.join(work_folder, ".git")):
            git_st = subprocess.run(
                ["git", "status", "--short"],
                cwd=work_folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            ).stdout.strip()
            git_diff = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=work_folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            ).stdout.strip()
            if git_st or git_diff:
                diff_info = f"\n\nТекущий Git статус:\n{git_st}\nИзменения:\n{git_diff}"
    except Exception:
        pass

    skill = load_skill("code-review")
    prompt = (
        "Ты выступаешь в роли старшего ревьюера кода. Проверь изменения в проекте.\n"
        f"Рабочая папка: {work_folder}\n"
        f"Фокус проверки: {focus if focus else 'Качество кода, логические ошибки, архитектура, безопасность'}\n"
        f"{diff_info}\n\n"
        f"{skill}\n\n"
        "ВАЖНО: Не изменяй файлы проекта! Изучи файлы и верни краткий, чёткий структурированный список замечаний и рекомендаций "
        "(критические баги, предупреждения, улучшения). Если код чистый и всё в порядке, подтверди это."
    )
    return run_claude(work_folder, prompt, tools_arg="Read,Grep,Glob")

def handle_ask(work_folder, question):
    prompt = (
        f"Вопрос по кодовой базе в {work_folder}:\n"
        f"{question}\n\n"
        "ВАЖНО: Ответь развёрнуто и конструктивно. Не изменяй файлы проекта напрямую."
    )
    return run_claude(work_folder, prompt, tools_arg="Read,Grep,Glob")

def handle_implement(work_folder, instruction):
    verification = load_skill("verification-before-completion")
    prompt = (
        f"Задача для реализации в проекте {work_folder}:\n"
        f"{instruction}\n\n"
        "Выполни необходимые изменения в коде аккуратно и точно."
        + (f"\n\n{verification}" if verification else "")
    )
    return run_claude(work_folder, prompt, allow_writes=True)

def handle_model_ask(provider_name, question, work_folder="."):
    config_data = load_providers()
    providers = config_data.get("providers", {})
    
    if not provider_name:
        provider_name = config_data.get("default_provider", "claude")
        
    if provider_name not in providers:
        available = ", ".join(providers.keys())
        return f"PROVIDER_ERROR: Провайдер '{provider_name}' не найден. Доступные: {available}"
        
    prov = providers[provider_name]
    ptype = prov.get("type")
    
    if ptype == "cli":
        return run_claude(work_folder, question, tools_arg="Read,Grep,Glob", model=prov.get("model"))
    elif ptype == "openai_compatible":
        sys_prompt = f"Ты инженер-разработчик в связке AI Duo. Контекст рабочей директории: {work_folder}."
        return run_openai_compatible(prov, question, system_prompt=sys_prompt)
    else:
        return f"PROVIDER_ERROR: Неизвестный тип провайдера '{ptype}'"

def handle_models_list():
    config_data = load_providers()
    providers = config_data.get("providers", {})
    default_p = config_data.get("default_provider", "claude")
    
    lines = [
        f"### Реестр моделей AI Duo (включая FREE LLM API)\n",
        f"**Провайдер по умолчанию:** `{default_p}`\n",
        "| Провайдер | Тариф | Приватность | Модель | Статус | Назначение |",
        "|---|---|---|---|---|---|"
    ]
    
    for name, p in providers.items():
        ptype = p.get("type")
        model = p.get("model", "-")
        desc = p.get("description", "")
        tier = f"`{p.get('tier', 'custom')}`"
        privacy = f"`{p.get('privacy', 'private')}`"
        status = "[НЕИЗВЕСТНО]"
        
        if ptype == "cli":
            status = "[ГОТОВ]" if shutil.which(p.get("command", "claude")) else "[НЕ УСТАНОВЛЕН]"
        elif ptype == "openai_compatible":
            base_url = p.get("base_url", "").rstrip("/")
            test_url = f"{base_url}/models"
            test_headers = {}
            api_key = p.get("api_key")
            if not api_key and "api_key_env" in p:
                api_key = os.environ.get(p["api_key_env"], "")
            if api_key:
                test_headers["Authorization"] = f"Bearer {api_key}"
            try:
                ssl_context = None
                ca_path = r"C:\projects\tools\corporate_ca.pem"
                if os.path.exists(ca_path):
                    import ssl
                    try:
                        ssl_context = ssl.create_default_context(cafile=ca_path)
                    except Exception:
                        pass
                req = urllib.request.Request(test_url, method="GET", headers=test_headers)
                with urllib.request.urlopen(req, timeout=2.0, context=ssl_context):
                    status = "[ОНЛАЙН]"
            except urllib.error.HTTPError as he:
                if he.code in (401, 403):
                    status = "[ОНЛАЙН (нужен ключ)]" if not api_key else "[ОШИБКА КЛЮЧА]"
                elif he.code == 404:
                    status = "[ОНЛАЙН]"
                else:
                    status = f"[HTTP {he.code}]"
            except Exception:
                status = "[ОНЛАЙН]" if "pollinations" in base_url else "[ОФФЛАЙН]"
                
        is_def = " *(по умолчанию)*" if name == default_p else ""
        lines.append(f"| **{name}**{is_def} | {tier} | {privacy} | `{model}` | {status} | {desc} |")
        
    return "\n".join(lines)

def handle_agent_run(agent_name, task, skill_name=None, work_folder=None, with_context=True, extra_context=""):
    if not work_folder:
        work_folder = os.getcwd()
        
    agents_data = load_agents()
    agents = agents_data.get("agents", {})
    
    if not agent_name:
        agent_name = agents_data.get("default_agent", "developer")
        
    if agent_name not in agents:
        available = ", ".join(agents.keys())
        return f"AGENT_ERROR: Агент '{agent_name}' не найден. Доступные агенты: {available}"
        
    agent = agents[agent_name]
    role_name = agent.get("name", agent_name)
    role_desc = agent.get("description", "")
    
    active_skills = []
    skill_content = ""
    if skill_name:
        content = load_skill(skill_name)
        if content:
            skill_content += f"\n\n--- АКТИВНЫЙ НАВЫК: {skill_name} ---\n{content}"
            active_skills.append(skill_name)
    else:
        for def_skill in agent.get("skills", []):
            content = load_skill(def_skill)
            if content:
                skill_content += f"\n\n--- НАВЫК: {def_skill} ---\n{content}"
                active_skills.append(def_skill)
                
    system_prompt = (
        f"Ты — специализированный автономный агент AI Duo: {role_name}.\n"
        f"Твоя цель: {role_desc}\n"
        f"Рабочая директория проекта: {work_folder}\n"
        f"{skill_content}\n\n"
        "Выполняй задачу строго в соответствии с принципами и стандартами твоих подключенных навыков."
    )
    if extra_context:
        system_prompt += f"\n\n--- РЕЗУЛЬТАТЫ ПРЕДЫДУЩИХ ЭТАПОВ ---\n{extra_context}"

    # Модели через HTTP API не видят файлы: даём им карту репозитория (в стиле aider repo map),
    # чтобы код попадал в существующую структуру проекта, а не писался "в вакууме".
    repo_map = ""
    if with_context and os.path.isdir(work_folder):
        repo_map = repo_context.build_repo_map(work_folder, focus=task, max_chars=REPO_MAP_BUDGET)
    
    providers_chain = [agent.get("primary_provider", "claude")]
    providers_chain.extend(agent.get("fallback_providers", []))
    
    config_data = load_providers()
    known_providers = config_data.get("providers", {})
    
    last_error = ""
    for prov_name in providers_chain:
        if prov_name not in known_providers:
            continue
        prov = known_providers[prov_name]
        ptype = prov.get("type")
        log(f"Agent '{agent_name}' calling provider '{prov_name}' ({ptype})...")
        
        try:
            if ptype == "cli":
                full_prompt = f"{system_prompt}\n\nПоставленная задача:\n{task}"
                res = run_claude(work_folder, full_prompt, tools_arg=agent.get("allowed_tools", "Read,Grep,Glob"), model=prov.get("model"))
            elif ptype == "openai_compatible":
                api_system = f"{system_prompt}\n\n--- КАРТА РЕПОЗИТОРИЯ ---\n{repo_map}" if repo_map else system_prompt
                res = run_openai_compatible(prov, task, system_prompt=api_system)
            else:
                res = f"PROVIDER_ERROR: Неизвестный тип {ptype}"
                
            is_error_or_limit = (
                any(sig in res for sig in ("CLAUDE_LIMIT_REACHED", "PROVIDER_LIMIT_REACHED", "PROVIDER_OFFLINE"))
                or res.startswith(("CLAUDE_ERROR", "PROVIDER_ERROR"))
            )
            if not is_error_or_limit:
                skills_tag = f" [Навыки: {', '.join(active_skills)}]" if active_skills else ""
                header = f"### [Агент: {role_name} | Модель: {prov_name}]{skills_tag}\n\n"
                return header + res
            else:
                last_error = f"{prov_name}: {res}"
                log(f"Provider '{prov_name}' failed/limited, switching to fallback...")
        except Exception as e:
            last_error = f"{prov_name} error: {str(e)}"
            
    return f"AGENT_ERROR: Все провайдеры для агента '{agent_name}' недоступны. Последняя ошибка: {last_error}"

def handle_repo_map(work_folder, focus="", max_chars=None):
    return repo_context.build_repo_map(work_folder, focus=focus, max_chars=int(max_chars or 12000))

def handle_repo_pack(work_folder, focus="", paths=None, max_chars=None):
    if isinstance(paths, str):
        paths = [p for p in paths.split(",") if p.strip()]
    return repo_context.pack_repo(work_folder, focus=focus, paths=paths, max_chars=int(max_chars or 60000))

def handle_agents_parallel(agent_names, task, work_folder=None, judge=None):
    """Mixture-of-agents: несколько агентов решают задачу параллельно, судья сводит лучший ответ."""
    work_folder = work_folder or os.getcwd()
    if isinstance(agent_names, str):
        agent_names = [a.strip() for a in agent_names.split(",") if a.strip()]
    if not agent_names:
        return "AGENT_ERROR: Не указан ни один агент для параллельного запуска."

    workers = max(1, min(PARALLEL_WORKERS, len(agent_names)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda name: (name, handle_agent_run(name, task, work_folder=work_folder)), agent_names))

    successes = [(n, r) for n, r in results if not r.startswith(ERROR_PREFIXES)]
    report = "\n\n---\n\n".join(r for _, r in results)
    if not successes:
        return f"AGENT_ERROR: Ни один агент не справился.\n\n{report}"
    if not judge or len(successes) < 2:
        return report

    candidates = "\n\n".join(f"=== Вариант агента '{n}' ===\n{r}" for n, r in successes)
    judge_task = (
        f"Исходная задача:\n{task}\n\n"
        f"Ниже независимые решения нескольких агентов:\n{candidates}\n\n"
        "Сравни варианты: найди ошибки и противоречия, выбери сильные стороны каждого "
        "и выдай одно итоговое, проверенное решение. В конце кратко перечисли, что взято из какого варианта."
    )
    verdict = handle_agent_run(judge, judge_task, work_folder=work_folder, with_context=False)
    return f"{verdict}\n\n<details><summary>Исходные варианты</summary>\n\n{report}\n\n</details>"

DEFAULT_PIPELINE = ["planner", "developer", "reviewer"]

def handle_agent_pipeline(task, stages=None, work_folder=None):
    """Конвейер агентов (spec -> plan -> implement -> review): каждый этап видит результаты предыдущих."""
    work_folder = work_folder or os.getcwd()
    if isinstance(stages, str):
        stages = [s.strip() for s in stages.split(",") if s.strip()]
    stages = stages or DEFAULT_PIPELINE

    outputs = []
    for stage in stages:
        context = "\n\n".join(f"=== Этап '{name}' ===\n{out}" for name, out in outputs)
        res = handle_agent_run(stage, task, work_folder=work_folder, extra_context=context)
        if res.startswith(ERROR_PREFIXES):
            done = ", ".join(n for n, _ in outputs) or "нет"
            return f"AGENT_ERROR: Конвейер остановлен на этапе '{stage}' (завершены: {done}).\n{res}\n\n{context}"
        outputs.append((stage, res))
    return "\n\n---\n\n".join(out for _, out in outputs)

def handle_agents_list():
    agents_data = load_agents()
    agents = agents_data.get("agents", {})
    lines = [
        "### База агентов AI Duo (Agent Registry)\n",
        "| ID агента | Название роли | Основная модель | Резервные модели (Fallback) | Подключенные навыки | Назначение |",
        "|---|---|---|---|---|---|"
    ]
    for aid, a in agents.items():
        name = a.get("name", aid)
        primary = f"`{a.get('primary_provider', '-')}`"
        fallbacks = ", ".join(f"`{f}`" for f in a.get("fallback_providers", [])) or "-"
        skills = ", ".join(f"`{s}`" for s in a.get("skills", [])) or "-"
        desc = a.get("description", "")
        lines.append(f"| **{aid}** | {name} | {primary} | {fallbacks} | {skills} | {desc} |")
    return "\n".join(lines)

def handle_skills_list():
    candidate_dirs = [
        os.path.join(BASE_DIR, "skills"),
        os.path.expandvars(r"%USERPROFILE%\.aiduo\skills"),
        r"C:\projects\tools\skills"
    ]
    skills_found = {}
    for sdir in candidate_dirs:
        if os.path.isdir(sdir):
            for fname in os.listdir(sdir):
                if fname.endswith(".md") and fname[:-3] not in skills_found:
                    fpath = os.path.join(sdir, fname)
                    title = fname
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                            if first_line.startswith("#"):
                                title = first_line.lstrip("#").strip()
                    except Exception:
                        pass
                    skills_found[fname[:-3]] = title
                    
    lines = [
        "### Библиотека навыков AI Duo (Skills Library)\n",
        "| Название скилла (ID) | Описание / Специализация |",
        "|---|---|"
    ]
    for sid, desc in skills_found.items():
        lines.append(f"| `{sid}` | {desc} |")
    return "\n".join(lines)

def handle_soup_recipe(query=""):
    try:
        from soup_cli.recipes.catalog import search_recipes, list_recipes
        if query:
            results = search_recipes(query)
            if not results:
                return f"Рецепты по запросу '{query}' не найдены."
            out = [f"Найдено рецептов ({len(results)}):"]
            for r in results[:10]:
                out.append(f"- **{r.model}** ({r.task}, {r.size}): {r.description}")
            return "\n".join(out)
        else:
            all_r = list_recipes()
            out = [f"Всего доступных шаблонов/рецептов Soup ({len(all_r)}):"]
            for r in all_r[:10]:
                out.append(f"- **{r.model}** ({r.task}, {r.size}): {r.description}")
            return "\n".join(out)
    except Exception as e:
        return f"SOUP_ERROR: {str(e)}"

TOOLS = [
    {
        "name": "claude_review",
        "description": "Claude проверяет изменения в проекте, ничего не меняя. Возвращает список замечаний и рекомендаций.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_folder": {
                    "type": "string",
                    "description": "Абсолютный путь к рабочей папке проекта"
                },
                "focus": {
                    "type": "string",
                    "description": "Суть задачи или область для проверки"
                }
            },
            "required": ["work_folder"]
        }
    },
    {
        "name": "claude_ask",
        "description": "Claude отвечает на сложный вопрос по проекту, архитектуре или алгоритму, без внесения правок.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_folder": {
                    "type": "string",
                    "description": "Абсолютный путь к рабочей папке проекта"
                },
                "question": {
                    "type": "string",
                    "description": "Вопрос для Claude"
                }
            },
            "required": ["work_folder", "question"]
        }
    },
    {
        "name": "claude_implement",
        "description": "Claude сам вносит изменения в файлы проекта по инструкции. Используется только в крайних случаях.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_folder": {
                    "type": "string",
                    "description": "Абсолютный путь к рабочей папке проекта"
                },
                "instruction": {
                    "type": "string",
                    "description": "Инструкция для реализации"
                }
            },
            "required": ["work_folder", "instruction"]
        }
    },
    {
        "name": "agent_run",
        "description": "Запустить задачу через специализированного агента из нашей базы (planner, architect, developer, tester, debugger, reviewer, security_auditor, llmops, hermes_agent) с подключенным скиллом. API-моделям автоматически передаётся карта репозитория.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Имя агента: 'planner', 'architect', 'developer', 'tester', 'debugger', 'reviewer', 'security_auditor', 'llmops', 'hermes_agent'"
                },
                "task": {
                    "type": "string",
                    "description": "Описание задачи или код для анализа"
                },
                "skill": {
                    "type": "string",
                    "description": "Опциональный ID скилла (например: 'spec-driven-development', 'writing-plans', 'test-driven-development', 'systematic-debugging', 'code-review', 'security-audit', 'architecture-audit', 'boilerplate-gen')"
                },
                "work_folder": {
                    "type": "string",
                    "description": "Рабочая папка проекта"
                },
                "with_context": {
                    "type": "boolean",
                    "description": "Передавать API-моделям карту репозитория (по умолчанию true)"
                }
            },
            "required": ["agent", "task"]
        }
    },
    {
        "name": "agents_list",
        "description": "Вывести список всех агентов из нашей базы, их роли, модели и подключенные навыки.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "skills_list",
        "description": "Вывести список всех доступных навыков (skills) для агентов AI Duo.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "model_ask",
        "description": "Задать вопрос любой модели из реестра провайдеров AI Duo (Claude, Free LLM API, Ollama, DeepSeek, Soup).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Имя провайдера (например: 'claude', 'pollinations', 'groq', 'openrouter_free', 'github_models', 'ollama', 'deepseek')"
                },
                "question": {
                    "type": "string",
                    "description": "Вопрос или задача для модели"
                },
                "work_folder": {
                    "type": "string",
                    "description": "Рабочая папка проекта (по умолчанию текущая)"
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "models_list",
        "description": "Вывести список всех подключенных моделей, включая Free LLM API, с тарифами (free/premium), приватностью и онлайн-статусом.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "repo_map",
        "description": "Компактная карта репозитория (в стиле aider): файлы, классы, функции и сигнатуры, отсортированные по релевантности задаче. Даёт структуру проекта за ~5-10% токенов.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_folder": {"type": "string", "description": "Абсолютный путь к рабочей папке проекта"},
                "focus": {"type": "string", "description": "Задача или ключевые слова: релевантные файлы попадут в начало карты"},
                "max_chars": {"type": "integer", "description": "Бюджет символов (по умолчанию 12000)"}
            },
            "required": ["work_folder"]
        }
    },
    {
        "name": "repo_pack",
        "description": "Упаковать содержимое файлов проекта в один AI-friendly блок (в стиле repomix) с учётом .gitignore и бюджета символов.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_folder": {"type": "string", "description": "Абсолютный путь к рабочей папке проекта"},
                "focus": {"type": "string", "description": "Задача или ключевые слова для выбора самых релевантных файлов"},
                "paths": {"type": "array", "items": {"type": "string"}, "description": "Явный список файлов или папок (относительно work_folder)"},
                "max_chars": {"type": "integer", "description": "Бюджет символов (по умолчанию 60000)"}
            },
            "required": ["work_folder"]
        }
    },
    {
        "name": "agents_parallel",
        "description": "Mixture-of-agents: несколько агентов/моделей решают одну задачу параллельно, опциональный агент-судья сравнивает варианты и выдаёт лучший итог.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agents": {"type": "array", "items": {"type": "string"}, "description": "Список агентов, например ['developer', 'hermes_agent', 'architect']"},
                "task": {"type": "string", "description": "Задача для всех агентов"},
                "judge": {"type": "string", "description": "Агент-судья для синтеза итогового ответа (например 'reviewer'); без него возвращаются все варианты"},
                "work_folder": {"type": "string", "description": "Рабочая папка проекта"}
            },
            "required": ["agents", "task"]
        }
    },
    {
        "name": "agent_pipeline",
        "description": "Конвейер агентов (spec -> plan -> implement -> review): каждый этап получает результаты предыдущих. По умолчанию planner -> developer -> reviewer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Описание фичи или задачи"},
                "stages": {"type": "array", "items": {"type": "string"}, "description": "Порядок агентов, например ['planner', 'developer', 'tester', 'reviewer']"},
                "work_folder": {"type": "string", "description": "Рабочая папка проекта"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "soup_recipe",
        "description": "Поиск и просмотр рецептов/шаблонов моделей из LLM Soup для локального запуска или файн-тюнинга.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос (например: 'coder', 'qwen', 'llama', 'math')"
                }
            }
        }
    }
]

def main():
    if sys.platform == "win32":
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    log("ai-bridge MCP server starting...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            log(f"Failed to parse JSON: {e}")
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "ai-bridge",
                        "version": "2.2.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "ping":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            work_folder = args.get("work_folder", os.getcwd())

            log(f"Tool call: {tool_name}")
            try:
                if tool_name == "claude_review":
                    text = handle_review(work_folder, args.get("focus", ""))
                elif tool_name == "claude_ask":
                    text = handle_ask(work_folder, args.get("question", ""))
                elif tool_name == "claude_implement":
                    text = handle_implement(work_folder, args.get("instruction", ""))
                elif tool_name == "agent_run":
                    text = handle_agent_run(args.get("agent", ""), args.get("task", ""), args.get("skill"), work_folder,
                                            args.get("with_context", True))
                elif tool_name == "agents_list":
                    text = handle_agents_list()
                elif tool_name == "skills_list":
                    text = handle_skills_list()
                elif tool_name == "model_ask":
                    text = handle_model_ask(args.get("provider", "claude"), args.get("question", ""), work_folder)
                elif tool_name == "models_list":
                    text = handle_models_list()
                elif tool_name == "repo_map":
                    text = handle_repo_map(work_folder, args.get("focus", ""), args.get("max_chars"))
                elif tool_name == "repo_pack":
                    text = handle_repo_pack(work_folder, args.get("focus", ""), args.get("paths"), args.get("max_chars"))
                elif tool_name == "agents_parallel":
                    text = handle_agents_parallel(args.get("agents", []), args.get("task", ""), work_folder, args.get("judge"))
                elif tool_name == "agent_pipeline":
                    text = handle_agent_pipeline(args.get("task", ""), args.get("stages"), work_folder)
                elif tool_name == "soup_recipe":
                    text = handle_soup_recipe(args.get("query", ""))
                else:
                    text = f"Неизвестный инструмент: {tool_name}"

                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": text
                            }
                        ],
                        "isError": text.startswith(ERROR_PREFIXES)
                    }
                }
            except Exception as e:
                log(f"Error handling tool call: {traceback.format_exc()}")
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"BRIDGE_ERROR: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
                }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        else:
            if req_id is not None:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    main()
