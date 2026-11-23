"""Calculadora de precificação estratégica com penetração de mercado (pricing-strategy)."""

from typing import Optional
from pydantic import BaseModel, Field

from bot_99freelas.models.project import Project
from bot_99freelas.config import settings


class PricingEstimate(BaseModel):
    """Estimativa de precificação estruturada."""
    suggested_price: float = Field(description="Preço final sugerido para a proposta")
    standard_price: float = Field(description="Preço cheio padrão de mercado")
    discount_applied_percent: float = Field(description="Percentual de desconto de penetração")
    estimated_hours: float = Field(description="Horas estimadas de trabalho")
    effective_hourly_rate: float = Field(description="Taxa horária efetiva resultante")
    delivery_days: int = Field(description="Prazo sugerido de entrega em dias úteis")
    pricing_rationale: str = Field(description="Justificativa da estratégia de preço")


class PricingCalculator:
    """Calcula valores estratégicos focando na conquista rápida de reputação 5 estrelas."""

    def __init__(
        self,
        base_hourly_rate: float = 60.0,
        penetration_discount_percentage: Optional[float] = None,
        min_proposal_value: Optional[float] = None,
    ):
        self.base_hourly_rate = base_hourly_rate
        self.penetration_discount_percentage = (
            penetration_discount_percentage
            if penetration_discount_percentage is not None
            else settings.MARKET_DISCOUNT_PERCENTAGE
        )
        self.min_proposal_value = (
            min_proposal_value if min_proposal_value is not None else settings.MIN_BUDGET
        )

    def estimate_effort(self, project: Project) -> float:
        """Estima o esforço em horas com base na complexidade e descrição."""
        desc = project.description.lower()
        skills = [s.lower() for s in project.skills_required]
        
        # Base de horas por tamanho de escopo
        hours = 6.0

        if any(w in desc for w in ["simples", "ajuste", "correção", "rápido", "pequeno"]):
            hours = 3.0
        elif any(w in desc for w in ["integração", "api", "dashboard", "painel", "automação", "bot"]):
            hours = 12.0
        elif any(w in desc for w in ["completo", "sistema", "plataforma", "aplicativo", "saas"]):
            hours = 24.0

        # Complexidade adicional por número de requisitos/habilidades
        if len(skills) > 4:
            hours += 4.0

        return hours

    def calculate(self, project: Project) -> PricingEstimate:
        hours = self.estimate_effort(project)
        standard_price = hours * self.base_hourly_rate

        # Se o cliente já especificou um orçamento máximo, ponderamos para não estourar
        client_budget = project.budget_average
        if client_budget is not None and client_budget > 0:
            target_standard = min(standard_price, client_budget)
        else:
            target_standard = standard_price

        # Aplica o desconto de penetração estratégica
        discount_factor = 1.0 - (self.penetration_discount_percentage / 100.0)
        suggested_price = target_standard * discount_factor

        # Garante piso mínimo de viabilidade
        if suggested_price < self.min_proposal_value:
            suggested_price = self.min_proposal_value

        suggested_price = round(suggested_price, 2)
        effective_hourly = round(suggested_price / hours, 2) if hours > 0 else 0.0

        # Prazo proporcional às horas de esforço
        if hours <= 4:
            delivery_days = 1
        elif hours <= 12:
            delivery_days = 2
        elif hours <= 24:
            delivery_days = 4
        else:
            delivery_days = max(5, int(hours // 6))

        rationale = (
            f"Preço padrão de R$ {target_standard:.2f} com desconto de {self.penetration_discount_percentage}% "
            f"para entrada rápida e geração de avaliação 5 estrelas. "
            f"Esforço estimado de {hours:.0f}h com entrega em até {delivery_days} dias."
        )

        return PricingEstimate(
            suggested_price=suggested_price,
            standard_price=round(target_standard, 2),
            discount_applied_percent=self.penetration_discount_percentage,
            estimated_hours=hours,
            effective_hourly_rate=effective_hourly,
            delivery_days=delivery_days,
            pricing_rationale=rationale,
        )
