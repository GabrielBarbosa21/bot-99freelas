"""Gerenciamento de sessão autenticada e cookies para o 99Freelas."""

import json
from pathlib import Path
from typing import Optional, Dict
from bot_99freelas.config import BASE_DIR, settings

COOKIES_FILE = BASE_DIR / "session_cookies.json"


class FreelasSession:
    """Gerencia a persistência de cookies e autenticação no 99Freelas."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self, cookies_path: Path = COOKIES_FILE):
        self.cookies_path = cookies_path

    def save_cookies(self, cookies: Dict[str, str]) -> None:
        """Salva cookies de sessão em disco de forma segura."""
        with open(self.cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

    def load_cookies(self) -> Dict[str, str]:
        """Carrega cookies existentes."""
        if not self.cookies_path.exists():
            return {}
        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_cookie_header(self) -> Optional[str]:
        """Gera string do header Cookie a partir dos cookies salvos."""
        cookies = self.load_cookies()
        if not cookies:
            return None
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])

    def is_authenticated(self) -> bool:
        """Verifica se existem cookies de sessão gravados."""
        cookies = self.load_cookies()
        return bool(cookies)


session_manager = FreelasSession()
