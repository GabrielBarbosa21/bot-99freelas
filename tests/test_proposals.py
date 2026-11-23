"""Testes do gerador de propostas humanizadas."""

from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.proposals.generator import ProposalGenerator


def test_proposal_generation():
    generator = ProposalGenerator()
    project = Project(
        id="10",
        url="https://99freelas.com.br/project/10",
        title="Integração de Webhook com Telegram",
        description="Preciso integrar um webhook de pagamentos para disparar mensagem instantânea em grupo do Telegram.",
        category="Backend",
        budget_min=200.0,
        budget_max=350.0,
        client=ClientProfile(name="Carlos")
    )
    proposal = generator.generate(project)

    assert "Olá, Carlos!" in proposal.text
    assert "Integração de Webhook com Telegram" in proposal.text
    assert "Investimento" in proposal.text
    assert "Garantia" in proposal.text
    assert "chat do 99Freelas" in proposal.text
    assert proposal.price > 0
    assert proposal.delivery_days >= 1
