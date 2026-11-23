"""Testes do classificador de intenção e gerador de respostas do chat."""

import unittest
from bot_99freelas.chat.models import MessageIntent, ChatMessage
from bot_99freelas.chat.classifier import IntentClassifier
from bot_99freelas.chat.responder import ChatResponder


class TestChatModule(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()
        self.responder = ChatResponder()

    def test_closing_intent(self):
        analysis = self.classifier.classify("Gostei da sua proposta, como fazemos para começar?")
        self.assertEqual(analysis.intent, MessageIntent.CLOSING)

        msg = ChatMessage(id="m1", project_id="p1", sender_name="Thiago", text="Gostei da sua proposta, como fazemos para começar?")
        reply = self.responder.generate_reply(analysis, msg)
        self.assertIn("Aceitar Proposta", reply)
        self.assertIn("Thiago", reply)

    def test_scope_creep_detection_and_change_order(self):
        analysis = self.classifier.classify("Além disso, dá pra incluir uma integração com o WhatsApp também?")
        self.assertEqual(analysis.intent, MessageIntent.SCOPE_EXPANSION)
        self.assertTrue(analysis.is_scope_creep)

        msg = ChatMessage(id="m2", project_id="p1", sender_name="Lucas", text="Além disso, dá pra incluir uma integração com o WhatsApp também?")
        reply = self.responder.generate_reply(analysis, msg, original_price=300.0)
        self.assertIn("além do escopo", reply)
        self.assertIn("R$", reply)  # Oferta de change order precificado

    def test_price_negotiation_holding_ground(self):
        analysis = self.classifier.classify("Achei um pouco caro, você faz por menos?")
        self.assertEqual(analysis.intent, MessageIntent.PRICE_NEGOTIATION)

        msg = ChatMessage(id="m3", project_id="p1", sender_name="Carlos", text="Achei um pouco caro, você faz por menos?")
        reply = self.responder.generate_reply(analysis, msg, original_price=250.0)
        self.assertIn("garantia", reply.lower())
        self.assertIn("R$ 250.00", reply)


if __name__ == "__main__":
    unittest.main()
