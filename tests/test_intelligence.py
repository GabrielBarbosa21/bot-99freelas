"""Testes da camada de inteligência contextual."""

import unittest
from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.intelligence.context import ContextAnalyzer


class TestIntelligence(unittest.TestCase):
    def test_context_extraction(self):
        analyzer = ContextAnalyzer()
        project = Project(
            id="proj-api",
            url="https://99freelas.com.br/project/api",
            title="Criar Webhook e integração REST API em Python",
            description="Preciso conectar um webhook de pagamentos para atualizar banco PostgreSQL via FastAPI.",
            category="Backend",
            client=ClientProfile(name="Rafael"),
        )

        ctx = analyzer.analyze(project)

        self.assertTrue("integração" in ctx.client_pain.lower() or "conectar" in ctx.client_pain.lower())
        self.assertTrue(any(tech.lower() in ["python", "fastapi", "postgresql", "webhook", "rest api"] for tech in ctx.detected_technologies))
        self.assertGreater(len(ctx.hook_sentence), 20)
        self.assertIn("Rafael", project.client.name)


if __name__ == "__main__":
    unittest.main()
