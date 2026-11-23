"""Interface de linha de comando (CLI) para teste interativo do motor da Fase 1."""

import sys
import argparse
from bot_99freelas.models.project import Project, ClientProfile, BudgetType
from bot_99freelas.filters.relevance import ProjectFilter
from bot_99freelas.pricing.calculator import PricingCalculator
from bot_99freelas.proposals.generator import ProposalGenerator
from bot_99freelas.simulation import run_simulation


def test_custom_project(
    title: str,
    description: str,
    budget_min: float,
    budget_max: float,
    proposals_count: int,
    client_name: str = "Cliente",
    client_hiring_rate: float = 50.0,
) -> None:
    """Testa a avaliação e geração de proposta para um projeto específico."""
    client = ClientProfile(
        name=client_name,
        projects_published=10,
        projects_awarded=int(10 * (client_hiring_rate / 100.0)),
        rating=4.8,
        reviews_count=5,
    )

    project = Project(
        id="test-custom-1",
        url="https://99freelas.com.br/project/custom",
        title=title,
        description=description,
        category="Desenvolvimento",
        budget_min=budget_min,
        budget_max=budget_max,
        proposals_count=proposals_count,
        client=client,
    )

    filt = ProjectFilter()
    calc = PricingCalculator()
    gen = ProposalGenerator(pricing_calc=calc)

    print("=" * 60)
    print(f"📋 AVALIANDO PROJETO: {project.title}")
    print(f"💰 Orçamento informado: R$ {budget_min:.2f} a R$ {budget_max:.2f}")
    print(f"👥 Concorrência: {proposals_count} propostas já enviadas")
    print(f"⭐ Cliente: {client.name} (Taxa de contratação: {client.hiring_rate}%)")
    print("=" * 60)

    res = filt.evaluate(project)
    if not res.accepted:
        print("\n❌ PROJETO REJEITADO PELO FILTRO:")
        print(f"   Score: {res.score:.1f}/100")
        for reason in res.reasons:
            print(f"   - {reason}")
        for warn in res.warnings:
            print(f"   ⚠️ {warn}")
        return

    print("\n✅ PROJETO APROVADO!")
    print(f"   Score de relevância: {res.score:.1f}/100")
    for reason in res.reasons:
        print(f"   + {reason}")
    for warn in res.warnings:
        print(f"   ⚠️ {warn}")

    pricing = calc.calculate(project)
    print("\n💰 PRECIFICAÇÃO ESTRATÉGICA:")
    print(f"   Preço Padrão de Mercado: R$ {pricing.standard_price:.2f}")
    print(f"   Preço de Penetração ({pricing.discount_applied_percent}% off): R$ {pricing.suggested_price:.2f}")
    print(f"   Estimativa de Esforço: {pricing.estimated_hours:.0f} horas")
    print(f"   Prazo Sugerido de Entrega: {pricing.delivery_days} dia(s)")

    proposal = gen.generate(project, pricing=pricing)
    print("\n📝 PROPOSTA PERSONALIZADA GERADA:")
    print("-" * 50)
    print(proposal.text)
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description="Testador do Motor de Freelance (Fase 1)")
    parser.add_argument("--simulate", action="store_true", help="Executa a bateria de simulação com casos reais")
    parser.add_argument("--title", type=str, help="Título do projeto para teste")
    parser.add_argument("--desc", type=str, help="Descrição do projeto para teste")
    parser.add_argument("--min", type=float, default=200.0, help="Orçamento mínimo")
    parser.add_argument("--max", type=float, default=400.0, help="Orçamento máximo")
    parser.add_argument("--proposals", type=int, default=3, help="Número de propostas já enviadas")
    parser.add_argument("--client", type=str, default="Lucas", help="Nome do cliente")

    args = parser.parse_args()

    if args.title and args.desc:
        test_custom_project(
            title=args.title,
            description=args.desc,
            budget_min=args.min,
            budget_max=args.max,
            proposals_count=args.proposals,
            client_name=args.client,
        )
    else:
        run_simulation()


if __name__ == "__main__":
    main()
