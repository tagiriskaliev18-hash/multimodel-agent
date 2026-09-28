@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   ⚡ AI DUO: Установка связки на новый компьютер ⚡
echo ========================================================
echo.
echo [1/3] Копирование инструментов моста в C:\projects\tools...
mkdir "C:\projects\tools" 2>nul
copy /y "tools\claude_bridge.py" "C:\projects\tools\"

echo [2/3] Восстановление правил и MCP конфигурации...
mkdir "%USERPROFILE%\.gemini\config" 2>nul
xcopy /s /e /y /q "gemini_config\*" "%USERPROFILE%\.gemini\config\"
mkdir "%USERPROFILE%\.gemini\antigravity" 2>nul
if exist "gemini_antigravity\mcp_config.json" (
    copy /y "gemini_antigravity\mcp_config.json" "%USERPROFILE%\.gemini\antigravity\"
)

echo [3/3] Настройка завершена!
echo.
echo ========================================================
echo [ГОТОВО] Все правила, инструкции и MCP-мост перенесены!
echo.
echo Не забудьте на новом компьютере:
echo 1. Установить Node.js и Claude Code:
echo    npm install -g @anthropic-ai/claude-code
echo 2. Авторизоваться в Claude:
echo    claude
echo ========================================================
pause
