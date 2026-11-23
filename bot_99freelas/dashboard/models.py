"""Modelos de dados para o Kanban de tarefas e métricas do dashboard."""

from enum import Enum
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    TODO = "a_fazer"
    IN_PROGRESS = "em_andamento"
    REVIEW = "revisao_homologacao"
    DONE = "concluido"


class ProjectStatus(str, Enum):
    PROPOSAL_SENT = "proposta_enviada"
    ACCEPTED = "aceito_em_execucao"
    COMPLETED = "concluido_entregue"
    LOST = "recusado_perdido"


class KanbanTask(BaseModel):
    """Tarefa individual do quadro Kanban de um projeto aceito."""
    id: str
    project_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class DashboardMetrics(BaseModel):
    """Métricas executivas de performance e conversão."""
    proposals_sent_count: int = 0
    accepted_projects_count: int = 0
    conversion_rate_percent: float = 0.0
    total_revenue_earned: float = 0.0
    pipeline_value: float = 0.0
    connections_used_today: int = 0
    connections_remaining_today: int = 3
