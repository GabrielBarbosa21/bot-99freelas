"""Testes para os endpoints HTTP do Webhook e Configuração do WhatsApp (Card 6.4, 6.5, 6.6)."""

import json
import unittest
from unittest.mock import patch
from http.server import HTTPServer
import threading
import urllib.request

from bot_99freelas.dashboard.web import DashboardRequestHandler
from bot_99freelas.dashboard.auth import generate_session_token, SESSION_COOKIE_NAME
from bot_99freelas.storage.db import db
from bot_99freelas.notifier.whatsapp import whatsapp_service


class TestWhatsAppHTTPWebhook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), DashboardRequestHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.auth_token = generate_session_token("admin")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_webhook_public_evolution_format(self):
        """Valida que o webhook público recebe evento de mensagem do WhatsApp e não é bloqueado por autenticação."""
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                },
                "message": {
                    "conversation": "STATUS"
                }
            }
        }
        url = f"http://127.0.0.1:{self.port}/api/webhook/whatsapp"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("STATUS DA OPERAÇÃO", data.get("reply", ""))

    def test_webhook_ignores_from_me(self):
        """Valida que o webhook ignora mensagens enviadas por mim para evitar loop infinito."""
        payload = {
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": True,
                },
                "message": {
                    "conversation": "STATUS"
                }
            }
        }
        url = f"http://127.0.0.1:{self.port}/api/webhook/whatsapp"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("ignored"))

    def test_authenticated_whatsapp_config_endpoints(self):
        """Valida endpoints autenticados GET e POST /api/whatsapp/config."""
        url = f"http://127.0.0.1:{self.port}/api/whatsapp/config"
        headers = {
            "Cookie": f"{SESSION_COOKIE_NAME}={self.auth_token}",
            "Content-Type": "application/json",
        }

        # GET config
        req_get = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req_get, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            cfg = json.loads(resp.read().decode("utf-8"))
            self.assertIn("enabled", cfg)

        # POST config
        new_cfg = {
            "enabled": True,
            "api_url": "http://localhost:8080",
            "api_key": "test_api_key",
            "instance": "test_instance",
            "phone": "5511999998888",
        }
        req_post = urllib.request.Request(
            url,
            data=json.dumps(new_cfg).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req_post, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res.get("success"))
            self.assertEqual(res["config"]["phone"], "5511999998888")


if __name__ == "__main__":
    unittest.main()
