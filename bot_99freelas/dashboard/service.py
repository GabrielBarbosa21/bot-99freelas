"""Serviço de cálculo de métricas de faturamento e conversão (Card 4.1 & 4.3)."""

from typing import Dict, Any
from bot_99freelas.dashboard.models import DashboardMetrics
from bot_99freelas.storage.db import db
from bot_99freelas.config import settings


class DashboardService:
    """Calcula indicadores de faturamento acumulado, taxa de conversão e conexões."""

    def calculate_metrics(self) -> DashboardMetrics:
        proposals = db._data.get("proposals", [])
        total_proposals = len(proposals)

        # Propostas aceitas/concluídas
        accepted_props = [p for p in proposals if p.get("status") in ("accepted", "completed")]
        accepted_count = len(accepted_props)

        # Faturamento acumulado dos projetos aceitos/entregues
        total_revenue = sum(float(p.get("price", 0.0)) for p in accepted_props)

        # Pipeline em aberto (propostas enviadas ou aguardando aprovação)
        pipeline_props = [p for p in proposals if p.get("status") in ("pending_approval", "sent")]
        pipeline_value = sum(float(p.get("price", 0.0)) for p in pipeline_props)

        # Taxa de conversão
        conversion_rate = round((accepted_count / total_proposals * 100), 1) if total_proposals > 0 else 0.0

        used_today = db.get_today_connections_used()
        remaining_today = max(0, settings.MAX_CONNECTIONS_PER_DAY - used_today)

        return DashboardMetrics(
            proposals_sent_count=total_proposals,
            accepted_projects_count=accepted_count,
            conversion_rate_percent=conversion_rate,
            total_revenue_earned=round(total_revenue, 2),
            pipeline_value=round(pipeline_value, 2),
            connections_used_today=used_today,
            connections_remaining_today=remaining_today,
        )


dashboard_service = DashboardService()
