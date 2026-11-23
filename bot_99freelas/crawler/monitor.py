"""Monitor assíncrono contínuo de novos projetos (Daemon de Background)."""

import asyncio
import logging
import urllib.request
from typing import List, Optional
from datetime import datetime

from bot_99freelas.models.project import Project
from bot_99freelas.storage.db import db
from bot_99freelas.filters.relevance import ProjectFilter, FilterResult
from bot_99freelas.pricing.calculator import PricingCalculator
from bot_99freelas.proposals.generator import ProposalGenerator
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.crawler.parser import FreelasParser
from bot_99freelas.notifier.telegram import telegram_notifier
from bot_99freelas.crawler.submitter import proposal_submitter
from bot_99freelas.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreelasMonitor")


class FreelasMonitor:
    """Serviço contínuo para monitoramento de novos projetos no 99Freelas."""

    FEED_URLS = [
        "https://www.99freelas.com.br/projects?categoria=web-mobile-e-software",
        "https://www.99freelas.com.br/projects",
    ]

    def __init__(
        self,
        check_interval_seconds: int = 60,  # 60 segundos por ciclo
        auto_send_threshold_score: float = 80.0,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.auto_send_threshold_score = auto_send_threshold_score
        self.project_filter = ProjectFilter()
        self.pricing_calc = PricingCalculator()
        self.proposal_gen = ProposalGenerator(pricing_calc=self.pricing_calc)

    async def fetch_latest_projects(self) -> List[Project]:
        """Busca projetos reais no feed do 99Freelas usando a sessão autenticada."""
        cookie_header = session_manager.get_cookie_header()
        headers = {
            **session_manager.DEFAULT_HEADERS,
            "Cookie": cookie_header or "",
        }

        all_projects: List[Project] = []
        for url in self.FEED_URLS:
            try:
                req = urllib.request.Request(url, headers=headers)
                # Executa a requisição HTTP em thread pool para não travar o event loop
                loop = asyncio.get_event_loop()
                html = await loop.run_in_executor(
                    None,
                    lambda: urllib.request.urlopen(req, timeout=12).read().decode("utf-8", errors="ignore")
                )
                projects = FreelasParser.parse_projects_page(html)
                if projects:
                    all_projects.extend(projects)
                    break
            except Exception as e:
                logger.warning(f"Aviso ao consultar '{url}': {e}")

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

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔎 Novo Projeto: '{project.title}' (ID: {project.id})")
        print(f"   👥 Concorrência: {project.proposals_count} propostas | 👤 Cliente: {project.client.name} (⭐ {project.client.rating or 'Novo'})")

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
            print(f"   ❌ Descartado (Score: {eval_result.score:.1f}/100): {reasons_text}")
            return

        print(f"   ✅ APROVADO! Score de Relevância: {eval_result.score:.1f}/100")

        # 3. Validação de Conexões Diárias
        if not db.can_send_proposal_today():
            print("   ⚠️ Limite diário de conexões atingido! Guardado no banco para amanhã.")
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

        print(f"   💰 Preço Estratégico: R$ {proposal.price:.2f} (Prazo: {proposal.delivery_days} dias)")
        print(f"   📝 Proposta Gerada:\n   " + proposal.text.replace("\n", "\n   "))

        # 5. Despacho 100% Autônomo se o Score for alto
        if settings.AUTO_SUBMIT_ENABLED and eval_result.score >= settings.AUTO_SUBMIT_MIN_SCORE:
            print(f"\n   ⚡ [MODO AUTÔNOMO] Enviando proposta diretamente no 99Freelas...")
            sub_res = proposal_submitter.submit(project, proposal)
            if sub_res.success:
                print(f"   🚀 SUCESSO! Proposta despachada com sucesso no 99Freelas!")
            else:
                print(f"   ⚠️ Aviso no envio: {sub_res.message}")

        # 6. Notificação via Telegram (se habilitado)
        await telegram_notifier.send_proposal_alert(project, proposal)

    async def run_loop(self, single_run: bool = False) -> None:
        """Inicia o ciclo contínuo de monitoramento."""
        print("\n" + "=" * 65)
        print(" 🤖 MONITOR DO 99FREELAS EM EXECUÇÃO (FEED AO VIVO)")
        print(f" ⏱️ Intervalo de Varredura: a cada {self.check_interval_seconds} segundos")
        print(f" 🔌 Conexões Usadas Hoje: {db.get_today_connections_used()} / {settings.MAX_CONNECTIONS_PER_DAY}")
        print("=" * 65 + "\n")

        cycle = 1
        while True:
            try:
                now_str = datetime.now().strftime("%H:%M:%S")
                print(f"[{now_str}] 📡 [Ciclo #{cycle}] Varrendo feed de novos projetos do 99Freelas...")
                projects = await self.fetch_latest_projects()
                print(f"[{now_str}] 📋 {len(projects)} projetos encontrados na listagem atual.")

                new_count = 0
                for project in projects:
                    if not db.is_project_seen(project.id):
                        new_count += 1
                        await self.process_project(project)

                if new_count == 0:
                    print(f"[{now_str}] 😴 Nenhum projeto novo desde a última checagem.")

            except Exception as e:
                logger.error(f"Erro durante ciclo de varredura: {e}", exc_info=True)

            if single_run:
                break

            cycle += 1
            print(f"\n⏳ Aguardando {self.check_interval_seconds}s para a próxima varredura... (Ctrl+C para parar)\n")
            await asyncio.sleep(self.check_interval_seconds)
