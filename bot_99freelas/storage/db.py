"""Gerenciamento de armazenamento local estruturado para histórico e limites de conexão."""

import json
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
from bot_99freelas.config import BASE_DIR, settings

STORAGE_FILE = BASE_DIR / "bot_data.json"


class Database:
    """Controlador de persistência local para projetos vistos e cotas diárias."""

    def __init__(self, file_path: Optional[Path] = None, db_path: Optional[Path] = None):
        target_path = file_path or db_path or STORAGE_FILE
        self.file_path = Path(target_path)
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {
            "projects": {},
            "proposals": [],
            "daily_connections": {},
        }
        self._load()

    def _load(self) -> None:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                pass

    def _save(self) -> None:
        with self._lock:
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def is_project_seen(self, project_id: str) -> bool:
        """Verifica se um projeto já foi visto anteriormente."""
        return project_id in self._data.get("projects", {})

    def record_project(
        self,
        project_id: str,
        url: str,
        title: str,
        budget_min: Optional[float],
        budget_max: Optional[float],
        proposals_count: int,
        client_name: str,
        score: float,
        status: str,
        reasons: str,
    ) -> None:
        """Salva informações do projeto no histórico."""
        self._data.setdefault("projects", {})[project_id] = {
            "id": project_id,
            "url": url,
            "title": title,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "proposals_count": proposals_count,
            "client_name": client_name,
            "score": score,
            "status": status,
            "reasons": reasons,
            "first_seen_at": datetime.now().isoformat(),
        }
        self._save()

    def record_proposal(
        self,
        project_id: str,
        price: float,
        delivery_days: int,
        proposal_text: str,
        status: str = "draft",
    ) -> int:
        """Grava uma proposta gerada para o projeto."""
        proposals = self._data.setdefault("proposals", [])
        prop_id = len(proposals) + 1
        proposals.append({
            "id": prop_id,
            "project_id": project_id,
            "price": price,
            "delivery_days": delivery_days,
            "proposal_text": proposal_text,
            "status": status,
            "created_at": datetime.now().isoformat(),
        })
        self._save()
        return prop_id

    def get_today_connections_used(self) -> int:
        """Retorna o número de conexões gastas hoje."""
        today = date.today().isoformat()
        return self._data.setdefault("daily_connections", {}).get(today, 0)

    def increment_today_connections(self) -> int:
        """Registra o uso de uma conexão hoje."""
        today = date.today().isoformat()
        current = self._data.setdefault("daily_connections", {}).get(today, 0)
        self._data["daily_connections"][today] = current + 1
        self._save()
        return current + 1

    def can_send_proposal_today(self) -> bool:
        """Verifica se ainda é permitido enviar proposta hoje conforme limite."""
        return self.get_today_connections_used() < settings.MAX_CONNECTIONS_PER_DAY


db = Database()
