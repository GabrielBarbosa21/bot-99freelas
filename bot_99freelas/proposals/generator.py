"""Gerador de propostas persuasivas, contextualizadas e humanizadas (sales-automator)."""

from typing import Optional
from pydantic import BaseModel, Field

from bot_99freelas.models.project import Project
from bot_99freelas.pricing.calculator import PricingEstimate, PricingCalculator
from bot_99freelas.intelligence.context import ContextAnalyzer, ProjectContext


class GeneratedProposal(BaseModel):
    """Proposta gerada pronta para revisão e envio."""
    text: str = Field(description="Texto completo formatado da proposta")
    price: float = Field(description="Valor proposto em BRL")
    delivery_days: int = Field(description="Prazo de entrega em dias úteis")
    summary_hook: str = Field(description="Gancho inicial de captura de atenção")
    scope_protection_clause: str = Field(description="Delimitação de escopo inclusa")
    context: Optional[ProjectContext] = Field(default=None, description="Contexto semântico diagnosticado")


class ProposalGenerator:
    """Gera propostas altamente personalizadas baseadas no diagnóstico de contexto real."""

    def __init__(
        self,
        pricing_calc: Optional[PricingCalculator] = None,
        context_analyzer: Optional[ContextAnalyzer] = None,
    ):
        self.pricing_calc = pricing_calc or PricingCalculator()
        self.context_analyzer = context_analyzer or ContextAnalyzer()

    def generate(
        self,
        project: Project,
        pricing: Optional[PricingEstimate] = None,
        context: Optional[ProjectContext] = None,
    ) -> GeneratedProposal:
        estimate = pricing or self.pricing_calc.calculate(project)
        ctx = context or self.context_analyzer.analyze(project)

        # 1. Saudação e Gancho contextualizado na dor do cliente
        client_name = project.client.name if project.client.name and project.client.name != "Cliente" else ""
        greeting = f"Olá, {client_name}!" if client_name else "Olá!"
        hook = ctx.hook_sentence

        # 2. Diagnóstico da dor e abordagem sob medida
        tech_str = f" utilizando as melhores práticas em {', '.join(ctx.detected_technologies)}" if ctx.detected_technologies else ""
        
        methodology = (
            f"🎯 **Abordagem Proposta**:\n"
            f"{ctx.suggested_approach}{tech_str}.\n\n"
            "Para garantir agilidade e excelência na entrega, divido o fluxo em 3 etapas:\n"
            f"1. **Alinhamento Inicial**: Validação rápida dos acessos e requisitos específicos.\n"
            f"2. **Implementação Focada**: Desenvolvimento com testes constantes para validar cada detalhe.\n"
            f"3. **Entrega e Garantia**: Homologação com suporte gratuito de 7 dias pós-entrega."
        )

        # 3. Delimitação de Escopo (no-free-work)
        scope_clause = (
            "O valor proposto contempla todas as necessidades descritas no anúncio. "
            "Se você tiver demandas adicionais no futuro, combinamos facilmente à parte."
        )

        # 4. Chamada para Ação de Baixo Risco (Low-friction CTA)
        cta = (
            "Podemos bater um papo rápido aqui pelo chat do 99Freelas? "
            "Assim tiro uma dúvida breve sobre seu ambiente e já iniciamos de imediato."
        )

        # Montagem do texto final
        body = (
            f"{greeting}\n\n"
            f"{hook}\n\n"
            f"{methodology}\n\n"
            f"💰 **Investimento**: R$ {estimate.suggested_price:.2f} (prazo de {estimate.delivery_days} dia(s))\n"
            f"🛡️ **Garantia**: Suporte e ajustes incluídos para sua total tranquilidade.\n\n"
            f"{scope_clause}\n\n"
            f"{cta}\n\n"
            f"Um abraço e fico à disposição no chat!"
        )

        return GeneratedProposal(
            text=body,
            price=estimate.suggested_price,
            delivery_days=estimate.delivery_days,
            summary_hook=hook,
            scope_protection_clause=scope_clause,
            context=ctx,
        )
