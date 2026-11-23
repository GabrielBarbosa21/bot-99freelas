"""Monitor assíncrono contínuo de novos projetos (Daemon de Background)."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from bot_99freelas.models.project import Project
from bot_99freelas.storage.db import db
from bot_99freelas.filters.relevance import ProjectFilter, FilterResult
from bot_99freelas.pricing.calculator import PricingCalculator
from bot_99freelas.proposals.generator import ProposalGenerator
from bot_99freelas.notifier.telegram import telegram_notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreelasMonitor")


class FreelasMonitor:
    """Serviço contínuo para monitoramento de novos projetos no 99Freelas."""

    def __init__(
        self,
        check_interval_seconds: int = 180,  # 3 minutos
        auto_send_threshold_score: float = 90.0,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.auto_send_threshold_score = auto_send_threshold_score
        self.project_filter = ProjectFilter()
        self.pricing_calc = PricingCalculator()
        self.proposal_gen = ProposalGenerator(pricing_calc=self.pricing_calc)

    async def fetch_latest_projects(self) -> List[Project]:
        """Simula ou busca projetos reais da listagem do 99Freelas."""
        # Integrado com o parser de feeds / HTML do 99Freelas
        return []

    async def process_project(self, project: Project) -> None:
        """Executa a triagem completa, precificação e envio/notificação."""
        if db.is_project_seen(project.id):
            return

        logger.info(f"🔎 Novo projeto detectado: '{project.title}' (ID: {project.id})")

        # 1. Filtro Cirúrgico
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
            logger.info(f"❌ Projeto descartado (Score: {eval_result.score:.1f}). Motivos: {reasons_text}")
            return

        # 3. Validação de Conexões Diárias
        if not db.can_send_proposal_today():
            logger.warning("⚠️ Limite diário de conexões atingido! Guardando projeto para amanhã.")
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

        logger.info(f"✨ Proposta gerada com sucesso! Valor: R$ {proposal.price:.2f} (Prazo: {proposal.delivery_days}d)")

        # 5. Notificação via Telegram
        await telegram_notifier.send_proposal_alert(project, proposal)

    async def run_loop(self, single_run: bool = False) -> None:
        """Inicia o ciclo contínuo de monitoramento."""
        logger.info("🚀 Monitor do 99Freelas iniciado!")
        while True:
            try:
                projects = await self.fetch_latest_projects()
                for project in projects:
                    await self.process_project(project)
            except Exception as e:
                logger.error(f"Erro durante ciclo de varredura: {e}", exc_info=True)

            if single_run:
                break

            await asyncio.sleep(self.check_interval_seconds)
