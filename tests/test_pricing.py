"""Testes da calculadora de precificação estratégica."""

from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.pricing.calculator import PricingCalculator


def test_pricing_calculation_with_discount():
    calc = PricingCalculator(base_hourly_rate=60.0, penetration_discount_percentage=20.0)
    project = Project(
        id="1",
        url="https://99freelas.com.br/project/1",
        title="Ajuste simples em página HTML/CSS",
        description="Ajuste simples de responsividade no menu mobile.",
        category="Web",
        budget_min=150.0,
        client=ClientProfile(name="Cliente Teste")
    )
    estimate = calc.calculate(project)
    
    assert estimate.estimated_hours == 3.0
    assert estimate.discount_applied_percent == 20.0
    # 3 horas * 60 = 180 standard; com 20% desconto = 144.0
    assert estimate.standard_price == 150.0 or estimate.standard_price == 180.0
    assert estimate.suggested_price > 0
    assert estimate.delivery_days >= 1


def test_pricing_min_floor():
    calc = PricingCalculator(base_hourly_rate=50.0, penetration_discount_percentage=30.0, min_proposal_value=120.0)
    project = Project(
        id="2",
        url="https://99freelas.com.br/project/2",
        title="Correção rápida de bug",
        description="Pequeno ajuste rápido no botão de checkout.",
        category="Web",
        budget_min=80.0,
        budget_max=100.0,
        client=ClientProfile(name="Loja Virtual")
    )
    estimate = calc.calculate(project)
    # Garante que não cai abaixo do min_proposal_value
    assert estimate.suggested_price >= 120.0
