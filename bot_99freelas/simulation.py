"""Modo de simulação para testar o fluxo de ponta a ponta sem enviar propostas reais."""

import json
from typing import List
from bot_99freelas.models.project import Project, ClientProfile, BudgetType
from bot_99freelas.filters.relevance import ProjectFilter
from bot_99freelas.pricing.calculator import PricingCalculator
from bot_99freelas.proposals.generator import ProposalGenerator


MOCK_PROJECTS = [
    Project(
        id="proj-101",
        url="https://www.99freelas.com.br/project/detalhe/101",
        title="Criar Bot em Python para integração com Planilhas Google",
        description=(
            "Preciso de uma automação que leia dados de um endpoint REST e alimente uma "
            "planilha Google Sheets a cada 1 hora. O script deve rodar em background no Linux "
            "e registrar logs de erros."
        ),
        category="Desenvolvimento Web e Software",
        subcategories=["Python", "Google Sheets API", "Automação"],
        budget_min=300.0,
        budget_max=600.0,
        proposals_count=4,
        skills_required=["Python", "API", "Linux"],
        client=ClientProfile(
            name="Mariana",
            location="São Paulo, SP",
            projects_published=6,
            projects_awarded=4,
            rating=5.0,
            reviews_count=4,
        ),
    ),
    Project(
        id="proj-102",
        url="https://www.99freelas.com.br/project/detalhe/102",
        title="Desenvolvimento de clone completo do Mercado Livre e Shopee",
        description=(
            "Quero um marketplace igual a Shopee e Mercado Livre com aplicativo Android, iOS, "
            "painel do vendedor, painel do administrador, gateway de pagamento, cálculo de frete "
            "dos Correios e transportadoras. Orçamento final fechado em R$ 150."
        ),
        category="Desenvolvimento Web e Software",
        subcategories=["E-commerce", "Mobile"],
        budget_min=100.0,
        budget_max=150.0,
        proposals_count=1,
        skills_required=["React Native", "Node.js", "AWS"],
        client=ClientProfile(
            name="João",
            location="Rio de Janeiro, RJ",
            projects_published=1,
            projects_awarded=0,
            rating=None,
            reviews_count=0,
        ),
    ),
    Project(
        id="proj-103",
        url="https://www.99freelas.com.br/project/detalhe/103",
        title="Ganhe R$ 300 por dia avaliando marcas no celular",
        description=(
            "Vaga imediata para início hoje! Basta ter um celular com acesso à internet. "
            "Trabalhe em casa digitando notas e avaliando produtos. Chamar no whatsapp antes "
            "para liberar o cadastro."
        ),
        category="Administração",
        subcategories=["Digitação"],
        budget_min=500.0,
        budget_max=1000.0,
        proposals_count=35,
        skills_required=["Digitação"],
        client=ClientProfile(
            name="Agência Oportunidade",
            projects_published=2,
            projects_awarded=0,
        ),
    ),
]


def run_simulation() -> None:
    print("=" * 60)
    print("🚀 INICIANDO SIMULAÇÃO DE TRIAGEM E GERAÇÃO DE PROPOSTAS")
    print("=" * 60)

    project_filter = ProjectFilter()
    pricing_calc = PricingCalculator()
    proposal_gen = ProposalGenerator(pricing_calc=pricing_calc)

    for i, project in enumerate(MOCK_PROJECTS, 1):
        print(f"\n[{i}/{len(MOCK_PROJECTS)}] Analisando Projeto: {project.title}")
        print(f"🔗 URL: {project.url}")
        print(f"💰 Orçamento: R$ {project.budget_min} - R$ {project.budget_max} | Concorrência: {project.proposals_count} propostas")
        print(f"👤 Cliente: {project.client.name} (Taxa Contratação: {project.client.hiring_rate}%)")

        filter_result = project_filter.evaluate(project)

        if not filter_result.accepted:
            print("❌ PROJETO REJEITADO!")
            print(f"   Score: {filter_result.score:.1f}/100")
            for reason in filter_result.reasons:
                print(f"   - {reason}")
            continue

        print(f"✅ PROJETO APROVADO! Score: {filter_result.score:.1f}/100")
        for reason in filter_result.reasons:
            print(f"   + {reason}")

        pricing = pricing_calc.calculate(project)
        print("\n📊 ESTRATÉGIA DE PRECIFICAÇÃO:")
        print(f"   Preço de Tabela: R$ {pricing.standard_price:.2f}")
        print(f"   Preço Sugerido (Penetração): R$ {pricing.suggested_price:.2f} ({pricing.discount_applied_percent}% off)")
        print(f"   Esforço: {pricing.estimated_hours:.0f}h | Prazo: {pricing.delivery_days} dia(s)")
        print(f"   Racional: {pricing.pricing_rationale}")

        proposal = proposal_gen.generate(project, pricing=pricing)
        print("\n📝 PROPOSTA GERADA (PRONTA PARA REVISÃO/ENVIO):")
        print("-" * 50)
        print(proposal.text)
        print("-" * 50)


if __name__ == "__main__":
    run_simulation()
