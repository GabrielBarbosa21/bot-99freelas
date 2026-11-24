"""Testes do Controle Granular de Varredura e Filtros de Busca (Card 6.3)."""

import json
import time
import threading
import unittest
from http.server import HTTPServer
import urllib.request

from bot_99freelas.config import settings
from bot_99freelas.models.project import Project, ClientProfile
from bot_99freelas.storage.db import db
from bot_99freelas.filters.relevance import ProjectFilter
from bot_99freelas.dashboard.web import DashboardRequestHandler
from bot_99freelas.dashboard.auth import generate_session_token, SESSION_COOKIE_NAME


class TestSearchFilters(unittest.TestCase):
    def setUp(self):
        db._data["search_config"] = {
            "target_keywords": ["python", "scraping", "fastapi"],
            "blacklist_keywords": ["tcc", "monografia", "wordpress", "artigo cientifico"],
            "categories": ["web-mobile-e-software"],
            "max_proposals": 12,
            "min_budget": 150.0,
        }
        db._save()
        self.project_filter = ProjectFilter(min_budget=150.0, max_proposals=12)

    def test_blacklist_immediate_rejection(self):
        # Projeto com palavra da blacklist no título
        p_black = Project(
            id="p-black-1",
            title="Formatação e revisão de TCC urgente",
            description="Preciso de alguém para formatar meu trabalho acadêmico nas normas ABNT.",
            url="https://99freelas/1",
            category="Web, Mobile e Software",
            budget_min=200.0,
            budget_max=300.0,
            proposals_count=2,
            client=ClientProfile(name="Aluno", projects_published=1, projects_awarded=1),
        )
        res = self.project_filter.evaluate(p_black)
        self.assertFalse(res.accepted)
        self.assertEqual(res.score, 0.0)
        self.assertTrue(any("blacklist: 'tcc'" in r.lower() for r in res.reasons))

    def test_target_keywords_sniper_bonus(self):
        p_target = Project(
            id="p-target-1",
            title="Desenvolver Web Scraper em Python com FastAPI",
            description="Preciso de script para extrair dados de produtos diariamente.",
            url="https://99freelas/2",
            category="Web, Mobile e Software",
            budget_min=400.0,
            budget_max=800.0,
            proposals_count=3,
            client=ClientProfile(name="Empresa", projects_published=4, projects_awarded=3),
        )
        res = self.project_filter.evaluate(p_target)
        self.assertTrue(res.accepted)
        self.assertGreaterEqual(res.score, 80.0)
        self.assertTrue(any("Stack Sniper" in r for r in res.reasons))

    def test_dynamic_max_proposals_rejection(self):
        # 14 propostas > limite dinâmico de 12
        p_crowded = Project(
            id="p-crowded-1",
            title="Desenvolvimento de Script Python",
            description="Ajuste em script já existente para automação.",
            url="https://99freelas/3",
            category="Web, Mobile e Software",
            budget_min=300.0,
            budget_max=500.0,
            proposals_count=14,
            client=ClientProfile(name="Cliente", projects_published=2, projects_awarded=1),
        )
        res = self.project_filter.evaluate(p_crowded)
        self.assertFalse(res.accepted)
        self.assertTrue(any("14 > 12" in r for r in res.reasons))

    def test_db_search_config_persistence(self):
        saved = db.save_search_config({
            "target_keywords": "django, flask, docker",
            "blacklist_keywords": "digitacao, curriculo",
            "max_proposals": 8,
            "min_budget": 250.0,
        })
        self.assertEqual(saved["max_proposals"], 8)
        self.assertEqual(saved["min_budget"], 250.0)
        self.assertIn("django", saved["target_keywords"])
        self.assertIn("digitacao", saved["blacklist_keywords"])

        # Confirma recarregamento do DB
        reloaded = db.get_search_config()
        self.assertEqual(reloaded["max_proposals"], 8)
        self.assertIn("flask", reloaded["target_keywords"])


class TestSearchHttpEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.ADMIN_USERNAME = "admin"
        settings.ADMIN_PASSWORD = "testpassword456"
        settings.AUTH_ENABLED = True

        cls.port = 5597
        cls.server = HTTPServer(("127.0.0.1", cls.port), DashboardRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.token = generate_session_token("admin")
        self.cookie_hdr = f"{SESSION_COOKIE_NAME}={self.token}"

    def test_get_and_post_search_config(self):
        # 1. GET /api/search/config
        req_get = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/search/config",
            headers={"Cookie": self.cookie_hdr},
        )
        resp_get = urllib.request.urlopen(req_get)
        self.assertEqual(resp_get.status, 200)
        cfg = json.loads(resp_get.read().decode("utf-8"))
        self.assertIn("target_keywords", cfg)
        self.assertIn("blacklist_keywords", cfg)

        # 2. POST /api/search/config
        update_payload = json.dumps({
            "target_keywords": "python, bot, scraping, ia",
            "blacklist_keywords": "tcc, wordpress, design",
            "categories": "web-mobile-e-software",
            "max_proposals": 10,
            "min_budget": 120.0,
        }).encode("utf-8")
        req_post = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/search/config",
            data=update_payload,
            headers={"Cookie": self.cookie_hdr, "Content-Type": "application/json"},
        )
        resp_post = urllib.request.urlopen(req_post)
        self.assertEqual(resp_post.status, 200)
        res_data = json.loads(resp_post.read().decode("utf-8"))
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["config"]["max_proposals"], 10)
        self.assertIn("tcc", res_data["config"]["blacklist_keywords"])


if __name__ == "__main__":
    unittest.main()
