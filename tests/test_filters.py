"""Testes do motor de filtragem de projetos."""

from bot_99freelas.models.project import Project, ClientProfile, BudgetType
from bot_99freelas.filters.relevance import ProjectFilter


def test_spam_detection():
    filt = ProjectFilter()
    project = Project(
        id="1",
        url="https://99freelas.com.br/project/1",
        title="Trabalho fácil sem experiência ganhando 5000",
        description="Ganhe dinheiro digitando notas fiscais. Chamar no whatsapp antes.",
        category="Admin",
        client=ClientProfile(name="Spammer", projects_published=1)
    )
    res = filt.evaluate(project)
    assert not res.accepted
    assert res.score == 0.0
    assert any("spam" in r.lower() for r in res.reasons)


def test_excessive_proposals_rejected():
    filt = ProjectFilter(max_proposals=15)
    project = Project(
        id="2",
        url="https://99freelas.com.br/project/2",
        title="Criar Landing Page em React",
        description="Preciso de uma landing page para captação de leads de evento.",
        category="Web",
        budget_min=300.0,
        budget_max=500.0,
        proposals_count=22,  # > 15
        client=ClientProfile(name="Agência XYZ", projects_published=5, projects_awarded=3)
    )
    res = filt.evaluate(project)
    assert not res.accepted
    assert any("muitas propostas" in r.lower() for r in res.reasons)


def test_unrealistic_scope_budget_rejected():
    filt = ProjectFilter()
    project = Project(
        id="3",
        url="https://99freelas.com.br/project/3",
        title="Criar aplicativo completo estilo Uber",
        description="Quero um clone do Uber com app motorista, passageiro e painel administrativo.",
        category="Mobile",
        budget_min=100.0,
        budget_max=150.0,
        proposals_count=2,
        client=ClientProfile(name="Ideia Milionária", projects_published=1)
    )
    res = filt.evaluate(project)
    assert not res.accepted
    assert any("incompatível com orçamento irrealista" in r.lower() for r in res.reasons)


def test_valid_project_accepted():
    filt = ProjectFilter(min_budget=100.0)
    project = Project(
        id="4",
        url="https://99freelas.com.br/project/4",
        title="Desenvolver script de automação em Python",
        description="Preciso de um script para extrair relatórios diários de uma API e salvar em planilha Excel.",
        category="Python",
        budget_min=250.0,
        budget_max=400.0,
        proposals_count=3,
        client=ClientProfile(
            name="Empresa Tech",
            projects_published=10,
            projects_awarded=6,
            rating=4.9,
            reviews_count=5
        )
    )
    res = filt.evaluate(project)
    assert res.accepted
    assert res.score >= 70.0


def test_sniper_target_stack_bonus():
    filt = ProjectFilter(min_budget=100.0)
    project = Project(
        id="5",
        url="https://99freelas.com.br/project/5",
        title="Criar Bot de Web Scraping e Integração com API em Python",
        description="Desenvolver um scraper usando Playwright e FastAPI para automação de dados.",
        category="Python",
        budget_min=300.0,
        budget_max=600.0,
        proposals_count=2,
        client=ClientProfile(
            name="Cliente Premium",
            projects_published=5,
            projects_awarded=4,
            rating=5.0,
            reviews_count=4
        )
    )
    res = filt.evaluate(project)
    assert res.accepted
    assert res.score >= 90.0  # Sniper score
    assert any("Sniper" in r for r in res.reasons)


def test_out_of_scope_discard():
    filt = ProjectFilter()
    project = Project(
        id="6",
        url="https://99freelas.com.br/project/6",
        title="Criação de Logotipo e Identidade Visual para Loja",
        description="Preciso de um flyer e cartão de visita além do logo completo.",
        category="Design",
        budget_min=200.0,
        budget_max=300.0,
        client=ClientProfile(name="Loja Roupas", projects_published=1)
    )
    res = filt.evaluate(project)
    assert not res.accepted
    assert res.score == 0.0
    assert any("fora do escopo" in r.lower() for r in res.reasons)


def test_fast_delivery_bonus():
    filt = ProjectFilter(min_budget=100.0)
    project = Project(
        id="7",
        url="https://99freelas.com.br/project/7",
        title="Ajuste simples urgente em script Python",
        description="Preciso de uma correção rápida em um script de automação hoje mesmo.",
        category="Python",
        budget_min=150.0,
        budget_max=200.0,
        proposals_count=1,
        client=ClientProfile(name="Agência Rápida", projects_published=2)
    )
    res = filt.evaluate(project)
    assert res.accepted
    assert any("Quick Win" in r for r in res.reasons)

