"""Modelos de dados para o 99Freelas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class BudgetType(str, Enum):
    FIXED = "fixed"
    HOURLY = "hourly"
    UNDEFINED = "undefined"


class ClientProfile(BaseModel):
    """Informações e histórico do cliente."""
    name: str = "Cliente"
    location: Optional[str] = None
    member_since: Optional[str] = None
    projects_published: int = Field(default=0, ge=0)
    projects_awarded: int = Field(default=0, ge=0)  # Quantos projetos já contratou
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    reviews_count: int = Field(default=0, ge=0)

    @property
    def hiring_rate(self) -> float:
        """Taxa histórica de contratação (0 a 100%)."""
        if self.projects_published == 0:
            return 0.0
        return round((self.projects_awarded / self.projects_published) * 100, 1)


class Project(BaseModel):
    """Representação completa de um projeto publicado no 99Freelas."""
    id: str
    url: str
    title: str
    description: str
    category: str
    subcategories: List[str] = Field(default_factory=list)
    budget_type: BudgetType = BudgetType.FIXED
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    proposals_count: int = Field(default=0, ge=0)
    published_at: Optional[datetime] = None
    skills_required: List[str] = Field(default_factory=list)
    client: ClientProfile = Field(default_factory=ClientProfile)

    @property
    def budget_average(self) -> Optional[float]:
        """Calcula o orçamento médio ou retorna o valor disponível."""
        if self.budget_min is not None and self.budget_max is not None:
            return (self.budget_min + self.budget_max) / 2
        return self.budget_min or self.budget_max
