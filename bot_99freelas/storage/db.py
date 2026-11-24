"""Gerenciamento de armazenamento local estruturado para histórico e limites de conexão."""

import json
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
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

    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Retorna todas as propostas que aguardam aprovação humana com dados do projeto."""
        proposals = self._data.get("proposals", [])
        projects = self._data.get("projects", {})
        pending = []
        for prop in reversed(proposals):
            if prop.get("status") == "pending_approval":
                item = dict(prop)
                proj = projects.get(prop.get("project_id"), {})
                item["project_title"] = proj.get("title", "Projeto sem título")
                item["project_url"] = proj.get("url", "")
                item["client_name"] = proj.get("client_name", "Cliente")
                item["score"] = proj.get("score", 0.0)
                item["budget_min"] = proj.get("budget_min")
                item["budget_max"] = proj.get("budget_max")
                item["proposals_count"] = proj.get("proposals_count", 0)
                pending.append(item)
        return pending

    def approve_proposal(
        self,
        prop_id: int,
        edited_text: Optional[str] = None,
        price: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Aprova e despacha a proposta pendente, respeitando os limites diários."""
        if not self.can_send_proposal_today():
            return False, f"Limite diário de {settings.MAX_CONNECTIONS_PER_DAY} conexões atingido."

        proposals = self._data.get("proposals", [])
        target = None
        for p in proposals:
            if p.get("id") == prop_id:
                target = p
                break

        if not target:
            return False, f"Proposta #{prop_id} não encontrada."

        if target.get("status") != "pending_approval":
            return False, f"Proposta #{prop_id} não está pendente de aprovação (status atual: {target.get('status')})."

        if edited_text:
            target["proposal_text"] = edited_text.strip()
        if price is not None and price > 0:
            target["price"] = float(price)

        target["status"] = "sent"
        target["approved_at"] = datetime.now().isoformat()

        proj_id = target.get("project_id")
        if proj_id and proj_id in self._data.get("projects", {}):
            self._data["projects"][proj_id]["status"] = "proposal_sent"

        self.increment_today_connections()
        self._save()
        return True, f"Proposta #{prop_id} aprovada com sucesso! Conexão debitada ({self.get_today_connections_used()}/{settings.MAX_CONNECTIONS_PER_DAY})."

    def reject_proposal(self, prop_id: int, reason: Optional[str] = None) -> Tuple[bool, str]:
        """Descarta uma proposta pendente sem debitar conexões."""
        proposals = self._data.get("proposals", [])
        target = None
        for p in proposals:
            if p.get("id") == prop_id:
                target = p
                break

        if not target:
            return False, f"Proposta #{prop_id} não encontrada."

        target["status"] = "rejected"
        target["rejected_at"] = datetime.now().isoformat()
        if reason:
            target["rejection_reason"] = reason

        self._save()
        return True, f"Proposta #{prop_id} descartada sem gasto de conexão."


db = Database()
