"""Gerador de propostas persuasivas, personalizadas e humanizadas (sales-automator)."""

from typing import Optional
from pydantic import BaseModel, Field

from bot_99freelas.models.project import Project
from bot_99freelas.pricing.calculator import PricingEstimate, PricingCalculator


class GeneratedProposal(BaseModel):
    """Proposta gerada pronta para revisão e envio."""
    text: str = Field(description="Texto completo formatado da proposta")
    price: float = Field(description="Valor proposto em BRL")
    delivery_days: int = Field(description="Prazo de entrega em dias úteis")
    summary_hook: str = Field(description="Gancho inicial de captura de atenção")
    scope_protection_clause: str = Field(description="Delimitação de escopo inclusa")


class ProposalGenerator:
    """Gera propostas altamente personalizadas evitando o padrão 'copia e cola'."""

    def __init__(self, pricing_calc: Optional[PricingCalculator] = None):
        self.pricing_calc = pricing_calc or PricingCalculator()

    def generate(
        self,
        project: Project,
        pricing: Optional[PricingEstimate] = None,
        custom_intro: Optional[str] = None
    ) -> GeneratedProposal:
        estimate = pricing or self.pricing_calc.calculate(project)

        # 1. Gancho específico (Hook)
        client_name = project.client.name if project.client.name != "Cliente" else ""
        greeting = f"Olá, {client_name}!" if client_name else "Olá!"

        hook = f"Analisei os detalhes do seu projeto sobre '{project.title}' e entendi exatamente o objetivo principal."

        # 2. Diagnóstico e Abordagem em 3 Passos
        methodology = (
            "Para garantir uma entrega ágil e sem retrabalho, planejei a execução em 3 etapas:\n"
            f"1. **Alinhamento Inicial**: Validação rápida dos requisitos e acesso/ambiente.\n"
            f"2. **Implementação e Testes**: Desenvolvimento focado no objetivo com validações constantes.\n"
            f"3. **Entrega e Garantia**: Homologação conjunta e suporte de 7 dias para qualquer ajuste pós-entrega."
        )

        # 3. Delimitação de Escopo (no-free-work)
        scope_clause = (
            "O valor proposto cobre integralmente as funcionalidades descritas no anúncio. "
            "Se surgirem novas ideias ou expansões durante o processo, alinhamos facilmente à parte."
        )

        # 4. Chamada para Ação de Baixo Risco (Low-friction CTA)
        cta = (
            "Podemos conversar rapidamente aqui pelo chat do 99Freelas? "
            "Gostaria de tirar uma ou duas dúvidas breves para começarmos de imediato."
        )

        # Montagem do texto final elegante e direto
        body = (
            f"{greeting}\n\n"
            f"{hook}\n\n"
            f"{methodology}\n\n"
            f"💰 **Investimento**: R$ {estimate.suggested_price:.2f} (prazo de {estimate.delivery_days} dia(s))\n"
            f"🛡️ **Garantia**: Suporte e ajustes incluídos para sua total tranquilidade.\n\n"
            f"{scope_clause}\n\n"
            f"{cta}\n\n"
            f"Um abraço e fico no seu aguardo!"
        )

        return GeneratedProposal(
            text=body,
            price=estimate.suggested_price,
            delivery_days=estimate.delivery_days,
            summary_hook=hook,
            scope_protection_clause=scope_clause,
        )
