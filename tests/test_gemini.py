"""Testes unitários para integração com Google Gemini AI e respostas inteligentes."""

import unittest
import json
from unittest.mock import patch, MagicMock
from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.chat.models import ChatMessage, MessageIntent, IntentAnalysis
from bot_99freelas.intelligence.gemini import GeminiService
from bot_99freelas.chat.responder import ChatResponder
from bot_99freelas.filters.relevance import ProjectFilter


class TestGeminiIntegration(unittest.TestCase):

    def setUp(self):
        self.service = GeminiService(api_key="test_api_key_mock", model="gemini-1.5-flash")
        self.dummy_project = Project(
            id="proj_101",
            title="Desenvolvimento de Bot para Web Scraping em Python",
            description="Preciso de um script para coletar dados de produtos em um e-commerce diariamente e salvar em CSV.",
            budget_min=300.0,
            budget_max=600.0,
            category="Web, Mobile e Software",
            proposals_count=4,
            client=ClientProfile(name="Carlos Mendes", projects_published=5, projects_awarded=4, rating=4.9),
            url="https://99freelas.com.br/project/101"
        )

    def test_gemini_service_configured_check(self):
        configured_service = GeminiService(api_key="AIzaSyDummyKey123")
        self.assertTrue(configured_service.is_configured())

        empty_service = GeminiService(api_key="")
        empty_service._api_key = ""
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            self.assertFalse(empty_service.is_configured())

    @patch("urllib.request.urlopen")
    def test_evaluate_project_with_ai(self, mock_urlopen):
        mock_response = MagicMock()
        inner_json = '{"accepted": true, "score": 92.0, "reason": "Escopo bem definido em Python e orcamento justo.", "technical_angle": "Usar Playwright e Pandas"}'
        resp_data = {"candidates": [{"content": {"parts": [{"text": inner_json}]}}]}
        mock_response.read.return_value = json.dumps(resp_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        eval_result = self.service.evaluate_project(self.dummy_project)
        self.assertIsNotNone(eval_result)
        self.assertTrue(eval_result.get("accepted"))
        self.assertEqual(eval_result.get("score"), 92.0)
        self.assertIn("Python", eval_result.get("reason", ""))

    @patch("urllib.request.urlopen")
    def test_answer_client_message_with_ai(self, mock_urlopen):
        mock_response = MagicMock()
        reply_text = "Olá! Sim, tenho ampla experiência com extração de dados e envio em CSV. Posso iniciar hoje mesmo. Basta aceitar a proposta na plataforma!"
        resp_data = {"candidates": [{"content": {"parts": [{"text": reply_text}]}}]}
        mock_response.read.return_value = json.dumps(resp_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        message = ChatMessage(
            id="m1",
            project_id="proj_101",
            sender_name="Carlos Mendes",
            text="Você já fez algum bot de scraping antes? Quanto tempo leva?",
            is_from_me=False
        )

        reply = self.service.answer_client_message(message, self.dummy_project)
        self.assertIsNotNone(reply)
        self.assertIn("extração de dados", reply)
        self.assertIn("proposta", reply)

    @patch("bot_99freelas.intelligence.gemini.gemini_service.is_configured", return_value=True)
    @patch("bot_99freelas.intelligence.gemini.gemini_service.answer_client_message")
    def test_chat_responder_uses_gemini_when_configured(self, mock_answer, mock_is_conf):
        mock_answer.return_value = "Resposta personalizada gerada pelo Gemini AI com sucesso."

        responder = ChatResponder()
        msg = ChatMessage(id="m2", project_id="p1", sender_name="Ana", text="Dá desconto?", is_from_me=False)
        analysis = IntentAnalysis(intent=MessageIntent.PRICE_NEGOTIATION, confidence=0.9, is_scope_creep=False)

        reply = responder.generate_reply(analysis, msg)
        self.assertEqual(reply, "Resposta personalizada gerada pelo Gemini AI com sucesso.")

    @patch("bot_99freelas.intelligence.gemini.gemini_service.is_configured", return_value=False)
    def test_chat_responder_falls_back_when_gemini_not_configured(self, mock_is_conf):
        responder = ChatResponder()
        msg = ChatMessage(id="m3", project_id="p1", sender_name="Ana", text="Dá desconto?", is_from_me=False)
        analysis = IntentAnalysis(intent=MessageIntent.PRICE_NEGOTIATION, confidence=0.9, is_scope_creep=False)

        reply = responder.generate_reply(analysis, msg, original_price=300.0)
        self.assertIn("R$ 300.00", reply)
        self.assertIn("condição promocional", reply)

    @patch("bot_99freelas.intelligence.gemini.gemini_service.is_configured", return_value=True)
    @patch("bot_99freelas.intelligence.gemini.gemini_service.evaluate_project")
    def test_project_filter_integrates_gemini_score(self, mock_eval, mock_is_conf):
        mock_eval.return_value = {
            "accepted": True,
            "score": 95.0,
            "reason": "Excelente projeto de automação",
            "technical_angle": "Python Playwright"
        }

        pfilter = ProjectFilter(min_budget=100.0)
        result = pfilter.evaluate(self.dummy_project)

        self.assertTrue(result.accepted)
        self.assertTrue(any("IA Gemini" in r for r in result.reasons))


if __name__ == "__main__":
    unittest.main()
