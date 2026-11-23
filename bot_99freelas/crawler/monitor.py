"""Monitor assíncrono contínuo de novos projetos com resiliência 24h e integração Web (Cards 5.1 & 5.3)."""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import urllib.request
from typing import List, Optional, Callable
from datetime import datetime
from pathlib import Path

from bot_99freelas.models.project import Project
from bot_99freelas.storage.db import db
from bot_99freelas.filters.relevance import ProjectFilter, FilterResult
from bot_99freelas.pricing.calculator import PricingCalculator
from bot_99freelas.proposals.generator import ProposalGenerator
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.crawler.parser import FreelasParser
from bot_99freelas.notifier.telegram import telegram_notifier
from bot_99freelas.crawler.submitter import proposal_submitter
from bot_99freelas.config import BASE_DIR, settings

# Configuração de rotação segura de logs em arquivo (Card 5.3)
LOGS_DIR = BASE_DIR / "logs"
try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

LOG_FILE = LOGS_DIR / "bot_99freelas.log"

logger = logging.getLogger("FreelasMonitor")
logger.setLevel(logging.INFO)

# Evita adicionar múltiplos handlers em reloads
if not logger.handlers:
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB por arquivo
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)
    except Exception:
        pass

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)


class FreelasMonitor:
    """Serviço contínuo para monitoramento resiliente de projetos no 99Freelas."""

    FEED_URLS = [
        "https://www.99freelas.com.br/projects?categoria=web-mobile-e-software",
        "https://www.99freelas.com.br/projects",
    ]

    def __init__(
        self,
        check_interval_seconds: int = 60,
        auto_send_threshold_score: float = 80.0,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.auto_send_threshold_score = auto_send_threshold_score
        self.log_callback = log_callback
        self.stop_requested = False

        self.project_filter = ProjectFilter()
        self.pricing_calc = PricingCalculator()
        self.proposal_gen = ProposalGenerator(pricing_calc=self.pricing_calc)

    def log(self, message: str, level: str = "info") -> None:
        """Emite mensagem de log para console, arquivo rotativo e callback web."""
        print(message)
        if level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        else:
            logger.info(message)

        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception:
                pass

    def stop(self) -> None:
        """Sinaliza parada imediata para o ciclo contínuo."""
        self.stop_requested = True

    async def _fetch_url_with_retry(self, url: str, headers: dict, max_retries: int = 3) -> Optional[str]:
        """Executa requisição HTTP resiliente com retentativas e backoff exponencial (Card 5.3)."""
        loop = asyncio.get_event_loop()
        for attempt in range(1, max_retries + 1):
            if self.stop_requested:
                return None
            try:
                req = urllib.request.Request(url, headers=headers)
                html = await loop.run_in_executor(
                    None,
                    lambda: urllib.request.urlopen(req, timeout=12).read().decode("utf-8", errors="ignore")
                )
                return html
            except Exception as e:
                backoff = 2 ** attempt
                if attempt < max_retries:
                    self.log(f"⚠️ [Tentativa {attempt}/{max_retries}] Falha na rede ao consultar '{url}': {e}. Reconectando em {backoff}s...", level="warning")
                    await asyncio.sleep(backoff)
                else:
                    self.log(f"❌ Erro definitivo ao consultar '{url}' após {max_retries} tentativas: {e}", level="error")
        return None

    async def fetch_latest_projects(self) -> List[Project]:
        """Busca projetos no feed do 99Freelas com resiliência contra falhas."""
        cookie_header = session_manager.get_cookie_header()
        headers = {
            **session_manager.DEFAULT_HEADERS,
            "Cookie": cookie_header or "",
        }

        all_projects: List[Project] = []
        for url in self.FEED_URLS:
            if self.stop_requested:
                break
            html = await self._fetch_url_with_retry(url, headers=headers)
            if html:
                projects = FreelasParser.parse_projects_page(html)
                if projects:
                    all_projects.extend(projects)
                    break

        # Remove duplicatas locais pelo ID
        unique = {}
        for p in all_projects:
            if p.id not in unique:
                unique[p.id] = p
        return list(unique.values())

    async def process_project(self, project: Project) -> None:
        """Executa a triagem completa, precificação e envio/notificação."""
        if db.is_project_seen(project.id):
            return

        self.log(f"🔎 Novo Projeto Detectado: '{project.title}' (ID: {project.id})")
        self.log(f"   👥 Concorrência: {project.proposals_count} propostas | 👤 Cliente: {project.client.name} (⭐ {project.client.rating or 'Novo'})")

        # 1. Filtro Sniper
        eval_result: FilterResult = self.project_filter.evaluate(project)

        # 2. Persistência do status de triagem
        status = "approved" if eval_result.accepted else "rejected"
        reasons_text = "; ".join(eval_result.reasons)
        db.record_project(
            project_id=project.id,
            url=project.url,
            title=project.title,
            budget_min=project.budget_min,
            budget_max=project.budget_max,
            proposals_count=project.proposals_count,
            client_name=project.client.name,
            score=eval_result.score,
            status=status,
            reasons=reasons_text,
        )

        if not eval_result.accepted:
            self.log(f"   ❌ Descartado (Score: {eval_result.score:.1f}/100): {reasons_text}")
            return

        self.log(f"   ✅ APROVADO! Score Sniper: {eval_result.score:.1f}/100")
        for r in eval_result.reasons:
            self.log(f"      • {r}")

        # 3. Validação de Conexões Diárias
        if not db.can_send_proposal_today():
            self.log("   ⚠️ Limite diário de conexões atingido! Guardado no banco para amanhã.")
            return

        # 4. Precificação e Geração de Proposta Contextualizada
        pricing = self.pricing_calc.calculate(project)
        proposal = self.proposal_gen.generate(project, pricing=pricing)

        db.record_proposal(
            project_id=project.id,
            price=proposal.price,
            delivery_days=proposal.delivery_days,
            proposal_text=proposal.text,
            status="pending_approval",
        )

        self.log(f"   💰 Preço Estratégico: R$ {proposal.price:.2f} (Prazo: {proposal.delivery_days} dias)")

        # 5. Despacho 100% Autônomo se o Score for alto
        if settings.AUTO_SUBMIT_ENABLED and eval_result.score >= settings.AUTO_SUBMIT_MIN_SCORE:
            self.log("   ⚡ [MODO AUTÔNOMO] Enviando proposta diretamente no 99Freelas...")
            sub_res = proposal_submitter.submit(project, proposal)
            if sub_res.success:
                self.log(f"   🚀 SUCESSO! Proposta despachada com sucesso no 99Freelas! ({project.title})")
            else:
                self.log(f"   ⚠️ Aviso no envio: {sub_res.message}", level="warning")

        # 6. Notificação via Telegram (se habilitado)
        try:
            await telegram_notifier.send_proposal_alert(project, proposal)
        except Exception as e:
            self.log(f"   ⚠️ Aviso Telegram: {e}", level="warning")

    async def run_loop(self, single_run: bool = False) -> None:
        """Inicia o ciclo contínuo de monitoramento resiliente 24h."""
        self.log("=" * 65)
        self.log(" 🤖 MONITOR 24H RESILIENTE DO 99FREELAS EM EXECUÇÃO")
        self.log(f" ⏱️ Intervalo de Varredura: a cada {self.check_interval_seconds} segundos")
        self.log(f" 🔌 Conexões Usadas Hoje: {db.get_today_connections_used()} / {settings.MAX_CONNECTIONS_PER_DAY}")
        self.log("=" * 65)

        cycle = 1
        while not self.stop_requested:
            try:
                # Validação periódica de saúde da sessão (Card 5.3)
                if cycle % 5 == 1:
                    health = session_manager.verify_session_health()
                    if not health["valid"]:
                        self.log(f"⚠️ Alerta de Sessão: {health['message']}", level="warning")

                self.log(f"📡 [Ciclo #{cycle}] Varrendo feed de novos projetos do 99Freelas...")
                projects = await self.fetch_latest_projects()
                self.log(f"📋 {len(projects)} projetos encontrados na listagem atual.")

                new_count = 0
                for project in projects:
                    if self.stop_requested:
                        break
                    if not db.is_project_seen(project.id):
                        new_count += 1
                        await self.process_project(project)

                if new_count == 0:
                    self.log("😴 Nenhum projeto novo desde a última checagem.")

                # Atualiza evento de scan no controller se importável
                try:
                    from bot_99freelas.crawler.controller import monitor_controller
                    monitor_controller.record_scan_event()
                except Exception:
                    pass

            except Exception as e:
                self.log(f"❌ Erro recuperável durante ciclo de varredura: {e}", level="error")

            if single_run or self.stop_requested:
                break

            cycle += 1
            self.log(f"⏳ Aguardando {self.check_interval_seconds}s para a próxima varredura...")

            # Sono fracionado para responder instantaneamente ao pedido de parada
            for _ in range(self.check_interval_seconds):
                if self.stop_requested:
                    break
                await asyncio.sleep(1)

        self.log("🛑 Ciclo de monitoramento finalizado.")
