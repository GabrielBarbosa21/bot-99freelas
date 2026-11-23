"""Testes do parser de HTML do 99Freelas."""

import unittest
from bot_99freelas.crawler.parser import FreelasParser


SAMPLE_HTML = """
<li class="result-item" data-id="12345">
    <h2 class="title"><a href="/projeto/12345-criar-script-python-de-automacao">Criar Script Python de Automação</a></h2>
    <div class="description">Preciso de um script que leia arquivos CSV e envie mensagens via API para clientes.</div>
    <div class="details">
        <span class="budget">Orçamento: R$ 300,00 a R$ 600,00</span>
        <span class="proposals">4 propostas</span>
        <span class="client">Carlos Silva</span>
    </div>
</li>
"""


class TestParser(unittest.TestCase):
    def test_parse_budget(self):
        min_b, max_b = FreelasParser.parse_budget_string("R$ 250,00 a R$ 500,00")
        self.assertEqual(min_b, 250.0)
        self.assertEqual(max_b, 500.0)

    def test_parse_project_block(self):
        project = FreelasParser.parse_project_block(SAMPLE_HTML)
        self.assertIsNotNone(project)
        self.assertEqual(project.id, "12345")
        self.assertIn("Criar Script Python", project.title)
        self.assertEqual(project.budget_min, 300.0)
        self.assertEqual(project.budget_max, 600.0)
        self.assertEqual(project.proposals_count, 4)
        self.assertIn("Carlos", project.client.name)

    def test_submitter_dry_run(self):
        from bot_99freelas.crawler.submitter import ProposalSubmitter
        from bot_99freelas.proposals.generator import GeneratedProposal
        from bot_99freelas.models.project import Project, ClientProfile

        submitter = ProposalSubmitter(dry_run=True)
        proj = Project(
            id="proj-dry-1",
            url="https://99freelas.com.br/project/dry",
            title="Projeto Teste",
            description="Descrição de teste",
            category="Web",
            client=ClientProfile(name="Ana"),
        )
        prop = GeneratedProposal(
            text="Proposta teste",
            price=200.0,
            delivery_days=2,
            summary_hook="Gancho",
            scope_protection_clause="Escopo",
        )
        res = submitter.submit(proj, prop)
        self.assertTrue(res.success)
        self.assertTrue(res.simulated)


if __name__ == "__main__":
    unittest.main()
