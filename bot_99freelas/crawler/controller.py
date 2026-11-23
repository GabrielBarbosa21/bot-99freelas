"""Controlador do Monitor em segundo plano para integração com o Painel Web (Card 5.1)."""

import asyncio
import threading
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

from bot_99freelas.crawler.monitor import FreelasMonitor
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.storage.db import db
from bot_99freelas.config import settings


class MonitorController:
    """Gerenciador de ciclo de vida do monitor 24h integrado ao servidor web."""

    def __init__(self, max_log_history: int = 150):
        self.max_log_history = max_log_history
        self._logs: deque = deque(maxlen=max_log_history)
        self._lock = threading.Lock()
        self._monitor: Optional[FreelasMonitor] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._last_scan_time: Optional[str] = None
        self._cycles_count = 0

    def add_log(self, message: str) -> None:
        """Registra um evento de log no buffer circular em memória."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        with self._lock:
            self._logs.append(entry)

    def get_logs(self, limit: int = 100) -> List[str]:
        """Retorna as mensagens de log mais recentes."""
        with self._lock:
            return list(self._logs)[-limit:]

    def clear_logs(self) -> None:
        """Limpa o histórico de logs."""
        with self._lock:
            self._logs.clear()

    @property
    def is_running(self) -> bool:
        """Informa se o monitor está ativo em execução."""
        return self._is_running and self._thread is not None and self._thread.is_alive()

    def start(self, interval_seconds: int = 60) -> Dict[str, Any]:
        """Inicia o monitor contínuo em background thread."""
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "O monitor já está em execução."}

            self._monitor = FreelasMonitor(
                check_interval_seconds=interval_seconds,
                log_callback=self.add_log,
            )
            self._is_running = True

            def _thread_target():
                self.add_log("🚀 Monitor unificado 24h iniciado com sucesso.")
                try:
                    asyncio.run(self._monitor.run_loop())
                except Exception as e:
                    self.add_log(f"❌ Erro fatal no monitor: {e}")
                finally:
                    self._is_running = False
                    self.add_log("🛑 Monitor 24h pausado.")

            self._thread = threading.Thread(target=_thread_target, daemon=True, name="FreelasMonitorWorker")
            self._thread.start()
            return {"success": True, "message": "Monitor ativado com sucesso."}

    def stop(self) -> Dict[str, Any]:
        """Solicita a interrupção suave do monitor contínuo."""
        with self._lock:
            if not self.is_running or not self._monitor:
                return {"success": False, "message": "O monitor já se encontra pausado."}

            self._monitor.stop()
            self._is_running = False
            self.add_log("⏳ Solicitando parada suave do monitor...")
            return {"success": True, "message": "Solicitação de parada enviada."}

    def record_scan_event(self) -> None:
        """Registra a conclusão de um ciclo de varredura."""
        self._last_scan_time = datetime.now().strftime("%d/%m %H:%M:%S")
        self._cycles_count += 1

    def get_status(self) -> Dict[str, Any]:
        """Retorna o estado operacional consolidado do monitor e sessão."""
        session_health = session_manager.verify_session_health()
        connections_today = db.get_today_connections_used()
        return {
            "active": self.is_running,
            "running": self.is_running,
            "cycles_completed": self._cycles_count,
            "last_scan": self._last_scan_time or "Nenhuma varredura ainda",
            "connections_used": connections_today,
            "max_connections": settings.MAX_CONNECTIONS_PER_DAY,
            "auto_submit_enabled": settings.AUTO_SUBMIT_ENABLED,
            "auto_submit_min_score": settings.AUTO_SUBMIT_MIN_SCORE,
            "session_valid": session_health["valid"],
            "session_message": session_health["message"],
        }


# Instância global compartilhada
monitor_controller = MonitorController()
