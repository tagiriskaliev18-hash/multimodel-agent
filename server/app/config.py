import os
from pathlib import Path

# Paths
SERVER_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SERVER_DIR.parent

# Load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Fallback basic .env loader if python-dotenv not installed
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# Configuration Settings
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Provider Keys & URLs
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
POLLINATIONS_BASE_URL = os.environ.get("POLLINATIONS_BASE_URL", "https://text.pollinations.ai/openai").rstrip("/")

DEFAULT_PROVIDER = os.environ.get("AIDUO_DEFAULT_PROVIDER", "openai")
DEFAULT_MODEL = os.environ.get("AIDUO_DEFAULT_MODEL", "gpt-4o-mini")

# Static Directories
AI_CHAT_DIR = BASE_DIR / "ai-chat"
PORTAL_DIR = BASE_DIR / "portal"
HUD_DIR = BASE_DIR / "tools" / "hud"
DESIGN_KIT_DIR = BASE_DIR / "tools" / "design-kit"
PROVIDERS_FILE = BASE_DIR / "tools" / "providers.json"
AGENTS_FILE = BASE_DIR / "tools" / "agents.json"
