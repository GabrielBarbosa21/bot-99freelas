"""Configurações globais da aplicação com suporte a .env nativo."""

import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path) -> None:
    """Carrega variáveis do arquivo .env sem exigir bibliotecas de terceiros."""
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if key not in os.environ:
                os.environ[key] = val


# Carrega variáveis locais
load_env_file(BASE_DIR / ".env")


class Settings(BaseModel):
    """Configurações do sistema."""
    GITHUB_TOKEN: str = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    GITHUB_REPO: str = Field(default_factory=lambda: os.getenv("GITHUB_REPO", "GabrielBarbosa21/bot-99freelas"))

    FREELAS_EMAIL: str = Field(default_factory=lambda: os.getenv("FREELAS_EMAIL", ""))
    FREELAS_PASSWORD: str = Field(default_factory=lambda: os.getenv("FREELAS_PASSWORD", ""))

    MAX_CONNECTIONS_PER_DAY: int = Field(default_factory=lambda: int(os.getenv("MAX_CONNECTIONS_PER_DAY", "3")))
    MIN_BUDGET: float = Field(default_factory=lambda: float(os.getenv("MIN_BUDGET", "100.0")))
    MARKET_DISCOUNT_PERCENTAGE: float = Field(default_factory=lambda: float(os.getenv("MARKET_DISCOUNT_PERCENTAGE", "20.0")))

    # Parâmetros de Filtro e Busca Sniper (Card 6.3)
    MAX_PROPOSALS: int = Field(default_factory=lambda: int(os.getenv("MAX_PROPOSALS", "15")))
    TARGET_KEYWORDS: str = Field(
        default_factory=lambda: os.getenv(
            "TARGET_KEYWORDS",
            "python, automacao, scraping, bot, api, backend, ia, dados, script, playwright, selenium, fastapi",
        )
    )
    BLACKLIST_KEYWORDS: str = Field(
        default_factory=lambda: os.getenv(
            "BLACKLIST_KEYWORDS",
            "tcc, monografia, digitacao, trabalho academico, formatacao abnt, artigo cientifico",
        )
    )
    SEARCH_CATEGORIES: str = Field(
        default_factory=lambda: os.getenv("SEARCH_CATEGORIES", "web-mobile-e-software")
    )

    # Modo de Envio (Trava Human-in-the-Loop: falso por padrão para exigir aprovação)
    AUTO_SUBMIT_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("AUTO_SUBMIT_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    AUTO_SUBMIT_MIN_SCORE: float = Field(
        default_factory=lambda: float(os.getenv("AUTO_SUBMIT_MIN_SCORE", "80.0"))
    )

    # Segurança e Autenticação do Painel Web (Card 6.1)
    AUTH_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("AUTH_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    ADMIN_USERNAME: str = Field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin"))
    ADMIN_PASSWORD: str = Field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin123"))
    SESSION_SECRET: str = Field(
        default_factory=lambda: os.getenv("SESSION_SECRET", "bot99freelas-secure-session-key-change-me")
    )

    # Notificações no Telegram (Opcional)
    TELEGRAM_ALERT_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("TELEGRAM_ALERT_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    TELEGRAM_BOT_TOKEN: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    TELEGRAM_CHAT_ID: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    # Inteligência Artificial (Google Gemini)
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    )


settings = Settings()
