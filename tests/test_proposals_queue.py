"""Testes da Fila de Aprovação Humana e Redesign (Card 6.2)."""

import json
import time
import threading
import unittest
from http.server import HTTPServer
import urllib.request
from bot_99freelas.config import settings
from bot_99freelas.storage.db import db
from bot_99freelas.dashboard.web import DashboardRequestHandler
from bot_99freelas.dashboard.auth import generate_session_token, SESSION_COOKIE_NAME


class TestProposalsQueue(unittest.TestCase):
    def setUp(self):
        db._data["projects"] = {
            "proj-test-1": {
                "id": "proj-test-1",
                "title": "Desenvolver Web Scraper Python",
                "url": "https://www.99freelas.com.br/project/proj-test-1",
                "client_name": "Empresa Alfa",
                "budget_min": 300.0,
                "budget_max": 600.0,
                "proposals_count": 8,
                "score": 92.0,
                "status": "approved",
                "reasons": "Score alto",
            }
        }
        db._data["proposals"] = []
        db._data["daily_connections"] = {}
        db._save()

    def test_record_and_get_pending_proposals(self):
        prop_id = db.record_proposal(
            project_id="proj-test-1",
            price=350.0,
            delivery_days=3,
            proposal_text="Olá! Posso desenvolver seu web scraper com Playwright.",
            status="pending_approval",
        )
        self.assertEqual(prop_id, 1)

        pending = db.get_pending_proposals()
        self.assertEqual(len(pending), 1)
        item = pending[0]
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["project_title"], "Desenvolver Web Scraper Python")
        self.assertEqual(item["client_name"], "Empresa Alfa")
        self.assertEqual(item["price"], 350.0)
        self.assertEqual(item["score"], 92.0)

    def test_approve_proposal_flow(self):
        prop_id = db.record_proposal(
            project_id="proj-test-1",
            price=350.0,
            delivery_days=3,
            proposal_text="Texto rascunho",
            status="pending_approval",
        )

        initial_connections = db.get_today_connections_used()
        success, msg = db.approve_proposal(
            prop_id=prop_id,
            edited_text="Texto revisado e aprovado pelo usuário.",
            price=400.0,
        )

        self.assertTrue(success)
        self.assertIn("aprovada com sucesso", msg)

        # Conexão consumida
        self.assertEqual(db.get_today_connections_used(), initial_connections + 1)

        # Fila agora está vazia
        self.assertEqual(len(db.get_pending_proposals()), 0)

        # Status no banco é sent
        prop = db._data["proposals"][0]
        self.assertEqual(prop["status"], "sent")
        self.assertEqual(prop["price"], 400.0)
        self.assertEqual(prop["proposal_text"], "Texto revisado e aprovado pelo usuário.")

    def test_reject_proposal_flow(self):
        prop_id = db.record_proposal(
            project_id="proj-test-1",
            price=350.0,
            delivery_days=3,
            proposal_text="Texto rascunho",
            status="pending_approval",
        )

        initial_connections = db.get_today_connections_used()
        success, msg = db.reject_proposal(prop_id=prop_id, reason="Cliente suspeito")

        self.assertTrue(success)
        self.assertIn("descartada sem gasto", msg)

        # Nenhuma conexão foi consumida
        self.assertEqual(db.get_today_connections_used(), initial_connections)
        self.assertEqual(len(db.get_pending_proposals()), 0)

        prop = db._data["proposals"][0]
        self.assertEqual(prop["status"], "rejected")
        self.assertEqual(prop.get("rejection_reason"), "Cliente suspeito")


class TestProposalsHttpEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.ADMIN_USERNAME = "admin"
        settings.ADMIN_PASSWORD = "testpassword456"
        settings.AUTH_ENABLED = True

        cls.port = 5598
        cls.server = HTTPServer(("127.0.0.1", cls.port), DashboardRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        db._data["projects"] = {
            "proj-http-1": {
                "id": "proj-http-1",
                "title": "API FastAPI e PostgreSQL",
                "url": "https://www.99freelas.com.br/project/proj-http-1",
                "client_name": "Tech Corp",
                "score": 95.0,
                "status": "approved",
            }
        }
        db._data["proposals"] = []
        db._data["daily_connections"] = {}
        db._save()

        # Token autenticado
        self.token = generate_session_token("admin")
        self.cookie_hdr = f"{SESSION_COOKIE_NAME}={self.token}"

    def test_http_pending_and_approve_endpoints(self):
        # 1. Cria proposta pendente
        prop_id = db.record_proposal(
            project_id="proj-http-1",
            price=500.0,
            delivery_days=4,
            proposal_text="Posso desenvolver sua API em FastAPI.",
            status="pending_approval",
        )

        # 2. Consulta GET /api/proposals/pending
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/proposals/pending",
            headers={"Cookie": self.cookie_hdr},
        )
        resp = urllib.request.urlopen(req)
        self.assertEqual(resp.status, 200)
        pending = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], prop_id)
        self.assertEqual(pending[0]["project_title"], "API FastAPI e PostgreSQL")

        # 3. Dispara POST /api/proposals/approve
        approve_payload = json.dumps({
            "proposal_id": prop_id,
            "edited_text": "Texto ajustado via painel",
            "price": 550.0,
        }).encode("utf-8")
        req_approve = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/proposals/approve",
            data=approve_payload,
            headers={"Cookie": self.cookie_hdr, "Content-Type": "application/json"},
        )
        resp_approve = urllib.request.urlopen(req_approve)
        self.assertEqual(resp_approve.status, 200)
        res_data = json.loads(resp_approve.read().decode("utf-8"))
        self.assertTrue(res_data["success"])

        # 4. Verifica que fila agora está vazia
        req2 = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/proposals/pending",
            headers={"Cookie": self.cookie_hdr},
        )
        resp2 = urllib.request.urlopen(req2)
        pending2 = json.loads(resp2.read().decode("utf-8"))
        self.assertEqual(len(pending2), 0)


if __name__ == "__main__":
    unittest.main()
