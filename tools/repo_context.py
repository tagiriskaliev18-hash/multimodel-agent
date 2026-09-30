"""Сборка компактного контекста репозитория для моделей без доступа к файлам.

Идеи взяты из:
- aider (repo map): вместо целых файлов модель получает карту символов —
  классы, функции и их сигнатуры. Это даёт понимание структуры проекта
  за 5-10% токенов от полного кода.
- repomix / gitingest: упаковка выбранных файлов в один AI-friendly блок
  с учётом .gitignore и бюджета символов.

Только стандартная библиотека, чтобы мост запускался без зависимостей.
"""
import ast
import os
import re
import subprocess

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build",
    ".next", ".nuxt", "target", ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    "coverage", ".tox", "vendor",
}
TEXT_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt",
    ".cs", ".rb", ".php", ".swift", ".c", ".h", ".cpp", ".hpp", ".vue", ".svelte",
    ".md", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".sql", ".sh", ".bat",
    ".ps1", ".html", ".css", ".scss", ".txt", ".env.example", ".dockerfile",
}
TEXT_NAMES = {"Dockerfile", "Makefile", "docker-compose.yml", ".env.example", ".gitignore"}
MAX_FILE_BYTES = 200_000

# Регулярки для языков без встроенного парсера: достаточно для карты символов.
_GENERIC_PATTERNS = {
    (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"): [
        r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+\w+[^{]*",
        r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*\w+\s*\([^)]*\)",
        r"^\s*(?:export\s+)?(?:const|let)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>",
        r"^\s*(?:export\s+)?(?:interface|type|enum)\s+\w+",
    ],
    (".go",): [r"^func\s+(?:\([^)]*\)\s*)?\w+\s*\([^)]*\)", r"^type\s+\w+\s+(?:struct|interface)"],
    (".rs",): [r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+\w+\s*(?:<[^>]*>)?\s*\([^)]*\)",
               r"^\s*(?:pub\s+)?(?:struct|enum|trait|impl)\b[^{;]*"],
    (".java", ".kt", ".cs"): [
        r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:abstract\s+)?(?:data\s+)?(?:class|interface|enum|record)\s+\w+",
        r"^\s*(?:public|private|protected|internal)\s+(?:static\s+)?[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)",
        r"^\s*fun\s+\w+\s*\([^)]*\)",
    ],
    (".rb",): [r"^\s*(?:class|module)\s+\w+", r"^\s*def\s+[\w.?!]+"],
    (".php",): [r"^\s*(?:abstract\s+|final\s+)?class\s+\w+", r"^\s*(?:public|private|protected)?\s*(?:static\s+)?function\s+\w+\s*\([^)]*\)"],
}


def _is_text_file(path):
    name = os.path.basename(path)
    if name in TEXT_NAMES:
        return True
    return os.path.splitext(name)[1].lower() in TEXT_EXTS


def list_files(root):
    """Файлы проекта относительно root: git ls-files (уважает .gitignore) или обход дерева."""
    root = os.path.abspath(root)
    try:
        res = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=15,
        )
        if res.returncode == 0 and res.stdout.strip():
            files = [f for f in res.stdout.splitlines() if f.strip()]
            return sorted(f for f in files if not (set(f.split("/")) & SKIP_DIRS))
    except (OSError, subprocess.SubprocessError):
        pass

    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fname), root).replace(os.sep, "/")
            found.append(rel)
    return sorted(found)


def _read_text(path):
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return None
        with open(path, "rb") as f:
            raw = f.read()
        if b"\x00" in raw[:4096]:
            return None
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def _py_signature(node):
    args = [a.arg for a in node.args.posonlyargs + node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    args += [a.arg for a in node.args.kwonlyargs]
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({', '.join(args)})"


def _python_symbols(text):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    symbols = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(_py_signature(node))
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            symbols.append(f"class {node.name}({bases})" if bases else f"class {node.name}")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append("    " + _py_signature(sub))
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                symbols.append(f"{target.id} = ...")
    return symbols


def _generic_symbols(ext, text):
    for exts, patterns in _GENERIC_PATTERNS.items():
        if ext in exts:
            compiled = [re.compile(p) for p in patterns]
            out = []
            for line in text.splitlines():
                for rx in compiled:
                    m = rx.match(line)
                    if m:
                        out.append(re.sub(r"\s+", " ", m.group(0).strip()).rstrip("{ "))
                        break
            return out
    return []


def _markdown_headings(text):
    headings, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(r"^#{1,3}\s", line):
            headings.append(line.strip())
    return headings[:12]


def extract_symbols(rel_path, text):
    ext = os.path.splitext(rel_path)[1].lower()
    if ext == ".py":
        return _python_symbols(text)
    if ext == ".md":
        return _markdown_headings(text)
    return _generic_symbols(ext, text)


def _focus_terms(focus):
    return [t.lower() for t in re.findall(r"[\w\-]{3,}", focus or "")]


def _score(rel_path, text, symbols, terms):
    score = min(len(symbols), 40)
    if terms:
        low_path = rel_path.lower()
        low_text = text.lower() if text else ""
        for t in terms:
            if t in low_path:
                score += 100
            elif t in low_text:
                score += 20
    # Тесты и конфиги полезны, но не важнее основного кода.
    if "/test" in f"/{rel_path}" or rel_path.endswith((".json", ".lock")):
        score -= 5
    return score


def _collect(root, focus):
    root = os.path.abspath(root)
    terms = _focus_terms(focus)
    entries = []
    for rel in list_files(root):
        if not _is_text_file(rel):
            continue
        text = _read_text(os.path.join(root, rel))
        if text is None:
            continue
        symbols = extract_symbols(rel, text)
        entries.append((_score(rel, text, symbols, terms), rel, text, symbols))
    entries.sort(key=lambda e: (-e[0], e[1]))
    return entries


def build_repo_map(root, focus="", max_chars=12000):
    """Карта репозитория: файлы, отсортированные по релевантности, и их символы."""
    if not os.path.isdir(root):
        return f"REPO_ERROR: Папка '{root}' не найдена."
    entries = _collect(root, focus)
    header = f"# Repo map: {os.path.basename(os.path.abspath(root))} ({len(entries)} файлов)\n"
    parts = [header]
    used = len(header)
    omitted = 0
    for _, rel, _, symbols in entries:
        block = rel + ":\n" + "".join(f"  {s}\n" for s in symbols[:60]) if symbols else rel + "\n"
        if used + len(block) > max_chars:
            omitted += 1
            continue
        parts.append(block)
        used += len(block)
    if omitted:
        parts.append(f"... ещё {omitted} файлов не вошли в бюджет {max_chars} символов\n")
    return "".join(parts)


def pack_repo(root, focus="", paths=None, max_chars=60000):
    """Упаковка содержимого файлов в один блок (как repomix) с бюджетом символов.

    paths — явный список файлов/префиксов папок; иначе берутся самые релевантные focus.
    """
    if not os.path.isdir(root):
        return f"REPO_ERROR: Папка '{root}' не найдена."
    entries = _collect(root, focus)
    if paths:
        wanted = [p.strip().strip("/").replace("\\", "/") for p in paths if p.strip()]
        entries = [e for e in entries if any(e[1] == w or e[1].startswith(w + "/") for w in wanted)]
    parts = []
    used = 0
    skipped = []
    for _, rel, text, _ in entries:
        block = f'<file path="{rel}">\n{text.rstrip()}\n</file>\n'
        if used + len(block) > max_chars:
            skipped.append(rel)
            continue
        parts.append(block)
        used += len(block)
    if skipped:
        parts.append(f"<!-- не вошли в бюджет {max_chars} символов: {', '.join(skipped[:30])}"
                     f"{' ...' if len(skipped) > 30 else ''} -->\n")
    if not parts:
        return "REPO_ERROR: Не найдено подходящих текстовых файлов."
    return "".join(parts)
