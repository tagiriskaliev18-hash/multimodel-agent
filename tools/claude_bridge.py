import sys
import json
import os
import subprocess
import traceback

CLAUDE_PATH = os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe")
if not os.path.exists(CLAUDE_PATH):
    CLAUDE_PATH = "claude"

MODEL = os.environ.get("CLAUDE_BRIDGE_MODEL", "sonnet")

def log(msg):
    sys.stderr.write(f"[claude-bridge] {msg}\n")
    sys.stderr.flush()

def validate_work_folder(work_folder):
    if not work_folder or not os.path.isdir(work_folder):
        return False, f"CLAUDE_ERROR: Рабочая папка '{work_folder}' не найдена или не является директорией."
    return True, os.path.abspath(work_folder)

def run_claude(cwd, prompt, tools_arg=None, allow_writes=False):
    ok, validated_cwd = validate_work_folder(cwd)
    if not ok:
        return validated_cwd

    cmd = [CLAUDE_PATH, "-p", prompt, "--model", MODEL]
    if tools_arg is not None:
        cmd.extend(["--tools", tools_arg])
    if allow_writes:
        cmd.append("--dangerously-skip-permissions")
    
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

    prompt = (
        "Ты выступаешь в роли старшего ревьюера кода. Проверь изменения в проекте.\n"
        f"Рабочая папка: {work_folder}\n"
        f"Фокус проверки: {focus if focus else 'Качество кода, логические ошибки, архитектура, безопасность'}\n"
        f"{diff_info}\n\n"
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
    prompt = (
        f"Задача для реализации в проекте {work_folder}:\n"
        f"{instruction}\n\n"
        "Выполни необходимые изменения в коде аккуратно и точно."
    )
    return run_claude(work_folder, prompt, allow_writes=True)

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
    }
]

def main():
    if sys.platform == "win32":
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    log("claude-bridge MCP server starting...")
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
                        "name": "claude-bridge",
                        "version": "1.0.0"
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
                        "isError": text.startswith("CLAUDE_ERROR") or text.startswith("CLAUDE_LIMIT_REACHED")
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
                                "text": f"CLAUDE_ERROR: {str(e)}"
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
