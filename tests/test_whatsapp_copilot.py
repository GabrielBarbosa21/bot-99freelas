"""Testes unitários para o WhatsApp Copilot, Ponte de Chat e Relatório Horário (Cards 6.4, 6.5, 6.6)."""

import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.proposals.generator import GeneratedProposal
from bot_99freelas.notifier.whatsapp import WhatsAppNotifier
from bot_99freelas.chat.models import ChatMessage
from bot_99freelas.chat.monitor import chat_monitor
from bot_99freelas.storage.db import db
from bot_99freelas.config import settings


class TestWhatsAppCopilot(unittest.TestCase):

    def setUp(self):
        self.notifier = WhatsAppNotifier()
        self.notifier.enabled = False  # Modo seguro de simulação
        self.sample_client = ClientProfile(name="Startup Tech", rating=4.9, projects_published=8)
        self.sample_project = Project(
            id="proj_zap_101",
            url="https://www.99freelas.com.br/project/bot-python",
            title="Desenvolvimento de Bot Python",
            description="Criar automação de propostas no 99Freelas",
            category="Web, Mobile e Software",
            budget_min=1000.0,
            budget_max=2500.0,
            proposals_count=3,
            client=self.sample_client,
            score=92.0,
        )
        self.sample_proposal = GeneratedProposal(
            text="Olá Startup Tech! Desenvolvo bots profissionais e de alta confiabilidade em Python.",
            price=1500.0,
            delivery_days=4,
            summary_hook="Desenvolvo bots em Python.",
            scope_protection_clause="Escopo inclui integração e testes.",
        )

    def test_send_proposal_alert_formatting(self):
        """Verifica se o alerta de proposta contém título, score, cliente e instruções de aprovação."""
        with patch.object(self.notifier, "send_message", return_value=True) as mock_send:
            ok = self.notifier.send_proposal_alert(self.sample_project, self.sample_proposal, prop_id=77)
            self.assertTrue(ok)
            mock_send.assert_called_once()
            msg_text = mock_send.call_args[0][0]

            self.assertIn("NOVO PROJETO QUALIFICADO", msg_text)
            self.assertIn("Desenvolvimento de Bot Python", msg_text)
            self.assertIn("SIM 77", msg_text)
            self.assertIn("NAO 77", msg_text)
            self.assertIn("R$ 1500.00", msg_text)

    def test_command_sim_approve_proposal(self):
        """Testa aprovação de proposta via comando 'SIM <id>' no WhatsApp (Card 6.4)."""
        prop_id = db.record_proposal(
            project_id=self.sample_project.id,
            price=1200.0,
            delivery_days=3,
            proposal_text="Proposta para teste do WhatsApp",
            status="pending_approval",
        )

        initial_connections = db.get_today_connections_used()
        reply = self.notifier.process_incoming_command(f"SIM {prop_id}")

        self.assertIn(f"Proposta #{prop_id} Aprovada com Sucesso", reply)
        self.assertEqual(db.get_today_connections_used(), initial_connections + 1)

    def test_command_nao_reject_proposal(self):
        """Testa descarte de proposta via comando 'NAO <id>' no WhatsApp (Card 6.4)."""
        prop_id = db.record_proposal(
            project_id=self.sample_project.id,
            price=800.0,
            delivery_days=2,
            proposal_text="Proposta para descarte",
            status="pending_approval",
        )

        initial_connections = db.get_today_connections_used()
        reply = self.notifier.process_incoming_command(f"NAO {prop_id}")

        self.assertIn(f"Proposta #{prop_id} descartada", reply)
        # Nenhuma conexão deve ter sido gasta
        self.assertEqual(db.get_today_connections_used(), initial_connections)

    def test_command_status_and_fila(self):
        """Testa consulta de status e fila de espera no WhatsApp."""
        reply_status = self.notifier.process_incoming_command("STATUS")
        self.assertIn("STATUS DA OPERAÇÃO", reply_status)
        self.assertIn("Conexões Hoje", reply_status)

        reply_fila = self.notifier.process_incoming_command("FILA")
        self.assertIn("Fila de Aprovação", reply_fila)

    def test_command_chat_reply_bridge(self):
        """Testa a ponte bidirecional do chat via '/r <msg>' (Card 6.5)."""
        # Simula recebimento de mensagem do cliente
        chat_msg = ChatMessage(
            id="msg_chat_1",
            project_id="proj_zap_101",
            sender_name="Carlos Cliente",
            text="Qual é o seu prazo de entrega?",
            is_from_me=False,
        )
        chat_monitor.last_conversation = {
            "message_id": chat_msg.id,
            "project_id": chat_msg.project_id,
            "sender_name": chat_msg.sender_name,
            "text": chat_msg.text,
        }

        reply = self.notifier.process_incoming_command("/r Consigo entregar em 3 dias úteis!")
        self.assertIn("Mensagem enviada no chat do 99Freelas", reply)
        self.assertIn("Consigo entregar em 3 dias úteis!", reply)
        self.assertEqual(chat_monitor.last_conversation["last_reply_sent"], "Consigo entregar em 3 dias úteis!")

    def test_command_hourly_report(self):
        """Testa o comando 'RELATORIO' e geração de métricas periódicas (Card 6.6)."""
        report = self.notifier.generate_hourly_report()
        self.assertIn("RELATÓRIO HORÁRIO", report)
        self.assertIn("Varredura da Última Hora", report)
        self.assertIn("Conexões Diárias", report)

        reply_cmd = self.notifier.process_incoming_command("RELATORIO")
        self.assertIn("RELATÓRIO HORÁRIO", reply_cmd)

    def test_database_hourly_metrics(self):
        """Valida cálculo de métricas das últimas horas no banco de dados."""
        # Registra um projeto rejeitado recente
        db.record_project(
            project_id="proj_hourly_1",
            url="http://test",
            title="Projeto Teste Relatorio",
            budget_min=100.0,
            budget_max=200.0,
            proposals_count=20,
            client_name="Cliente Teste",
            score=30.0,
            status="rejected",
            reasons="Concorrência muito alta (20); Orçamento abaixo do piso",
        )

        metrics = db.get_hourly_metrics()
        self.assertIn("projects_scanned", metrics)
        self.assertIn("connections_used_today", metrics)
        self.assertGreaterEqual(metrics["projects_scanned"], 1)
        self.assertGreaterEqual(metrics["projects_rejected"], 1)


if __name__ == "__main__":
    unittest.main()
