@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   ⚡ AI DUO + LLM SOUP: Установка связки на ПК ⚡
echo ========================================================
echo.
echo [1/4] Копирование инструментов моста, базы агентов и навыков в C:\projects\tools...
mkdir "C:\projects\tools" 2>nul
copy /y "tools\claude_bridge.py" "C:\projects\tools\"
copy /y "tools\providers.json" "C:\projects\tools\"
copy /y "tools\agents.json" "C:\projects\tools\"
mkdir "C:\projects\tools\skills" 2>nul
xcopy /s /e /y /q "tools\skills\*" "C:\projects\tools\skills\"

echo [2/4] Восстановление правил и глобальной MCP конфигурации Gemini...
mkdir "%USERPROFILE%\.gemini\config" 2>nul
xcopy /s /e /y /q "gemini_config\*" "%USERPROFILE%\.gemini\config\"
mkdir "%USERPROFILE%\.gemini\antigravity" 2>nul
if exist "gemini_antigravity\mcp_config.json" (
    copy /y "gemini_antigravity\mcp_config.json" "%USERPROFILE%\.gemini\antigravity\"
)
if exist "gemini_antigravity\mcp" (
    mkdir "%USERPROFILE%\.gemini\antigravity\mcp" 2>nul
    xcopy /s /e /y /q "gemini_antigravity\mcp\*" "%USERPROFILE%\.gemini\antigravity\mcp\"
)

echo [3/4] Установка библиотеки LLM Soup (soup-cli + MCP)...
python -m pip install -q "soup-cli[mcp]"
if %errorlevel% neq 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Не удалось автоматически установить soup-cli[mcp]. Проверьте интернет или установите вручную: pip install "soup-cli[mcp]"
)

echo [4/4] Регистрация глобальных MCP серверов в Claude Code (user-scope)...
where claude >nul 2>nul
if %errorlevel% equ 0 (
    call claude mcp add soup -s user -- soup mcp serve >nul 2>nul
    call claude mcp add ai-bridge -s user -- python C:\projects\tools\claude_bridge.py >nul 2>nul
    echo      √ Claude Code MCP успешно настроен для всех проектов!
) else (
    echo      ! Claude Code не обнаружен в PATH. Зарегистрируйте после установки Node.js/Claude:
    echo        claude mcp add soup -s user -- soup mcp serve
    echo        claude mcp add ai-bridge -s user -- python C:\projects\tools\claude_bridge.py
)

echo.
echo ========================================================
echo [ГОТОВО] AI Duo теперь работает глобально во ВСЕХ проектах!
echo.
echo Подключенные компоненты:
echo 1. Gemini Antigravity (дирижёр/оркестратор)
echo 2. Claude Code CLI (старший ревьюер и архитектор)
echo 3. LLM Soup (реестр моделей, рецепты, адаптеры, MCP)
echo 4. Провайдеры дополнительных моделей: C:\projects\tools\providers.json
echo.
echo Для добавления локальной модели (Ollama):
echo   - Установите Ollama и выполните: ollama run qwen2.5-coder:1.5b
echo ========================================================
pause
