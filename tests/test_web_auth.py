"""Testes de segurança e autenticação do Painel Web (Card 6.1)."""

import time
import json
import threading
import unittest
from http.server import HTTPServer
import urllib.request
import urllib.error
from bot_99freelas.config import settings
from bot_99freelas.dashboard.web import DashboardRequestHandler
from bot_99freelas.dashboard.auth import (
    generate_session_token,
    verify_session_token,
    extract_session_token_from_cookie,
    is_request_authenticated,
    validate_credentials,
    check_rate_limit,
    record_failed_login,
    clear_failed_login,
    SESSION_COOKIE_NAME,
)


class TestWebAuth(unittest.TestCase):
    def setUp(self):
        settings.ADMIN_USERNAME = "testadmin"
        settings.ADMIN_PASSWORD = "SecretPassword123!"
        settings.AUTH_ENABLED = True

    def test_validate_credentials(self):
        self.assertTrue(validate_credentials("testadmin", "SecretPassword123!"))
        self.assertFalse(validate_credentials("testadmin", "wrongpass"))
        self.assertFalse(validate_credentials("wronguser", "SecretPassword123!"))

    def test_session_token_lifecycle(self):
        token = generate_session_token("testadmin")
        self.assertIsNotNone(token)
        self.assertEqual(len(token.split(".")), 3)

        # Validação correta
        username = verify_session_token(token)
        self.assertEqual(username, "testadmin")

        # Token adulterado
        tampered = token[:-4] + "abcd"
        self.assertIsNone(verify_session_token(tampered))

        # Token inválido
        self.assertIsNone(verify_session_token("invalid.token"))
        self.assertIsNone(verify_session_token(""))

    def test_extract_session_token(self):
        token = generate_session_token("admin")
        cookie_str = f"other_cookie=123; {SESSION_COOKIE_NAME}={token}; theme=dark"
        extracted = extract_session_token_from_cookie(cookie_str)
        self.assertEqual(extracted, token)

    def test_request_authenticated_headers(self):
        token = generate_session_token("admin")

        # Sem header
        self.assertFalse(is_request_authenticated({}))

        # Com cookie válido
        headers_cookie = {"Cookie": f"{SESSION_COOKIE_NAME}={token}"}
        self.assertTrue(is_request_authenticated(headers_cookie))

        # Com Bearer token válido
        headers_bearer = {"Authorization": f"Bearer {token}"}
        self.assertTrue(is_request_authenticated(headers_bearer))

        # Com token expirado/adulterado
        headers_bad = {"Cookie": f"{SESSION_COOKIE_NAME}=fake.token.123"}
        self.assertFalse(is_request_authenticated(headers_bad))

    def test_rate_limiting(self):
        ip = "192.168.100.99"
        clear_failed_login(ip)

        allowed, wait_sec = check_rate_limit(ip)
        self.assertTrue(allowed)
        self.assertEqual(wait_sec, 0)

        # 4 falhas ainda não bloqueiam
        for _ in range(4):
            record_failed_login(ip)
            allowed, _ = check_rate_limit(ip)
            self.assertTrue(allowed)

        # 5ª falha bloqueia
        record_failed_login(ip)
        allowed, wait_sec = check_rate_limit(ip)
        self.assertFalse(allowed)
        self.assertGreater(wait_sec, 0)

        # Limpeza desfaz o bloqueio
        clear_failed_login(ip)
        allowed, _ = check_rate_limit(ip)
        self.assertTrue(allowed)


class TestWebHttpIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.ADMIN_USERNAME = "admin"
        settings.ADMIN_PASSWORD = "testpassword456"
        settings.AUTH_ENABLED = True

        cls.port = 5599
        cls.server = HTTPServer(("127.0.0.1", cls.port), DashboardRequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_unauthenticated_redirect_to_login(self):
        # Desativa auto-redirect do urllib para verificar status 302
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp

        opener = urllib.request.build_opener(NoRedirectHandler)
        resp = opener.open(f"http://127.0.0.1:{self.port}/")
        self.assertEqual(resp.status, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_unauthenticated_api_401(self):
        url = f"http://127.0.0.1:{self.port}/api/metrics"
        try:
            urllib.request.urlopen(url)
            self.fail("Deveria retornar HTTP 401")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)
            body = json.loads(e.read().decode("utf-8"))
            self.assertIn("Acesso não autorizado", body.get("error", ""))

    def test_full_login_flow_and_authenticated_access(self):
        # 1. Tenta login com senha incorreta
        login_url = f"http://127.0.0.1:{self.port}/api/auth/web-login"
        bad_payload = json.dumps({"username": "admin", "password": "wrong"}).encode("utf-8")
        req_bad = urllib.request.Request(login_url, data=bad_payload, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req_bad)
            self.fail("Deveria retornar 401")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

        # 2. Login correto
        good_payload = json.dumps({"username": "admin", "password": "testpassword456"}).encode("utf-8")
        req_good = urllib.request.Request(login_url, data=good_payload, headers={"Content-Type": "application/json"})
        resp_good = urllib.request.urlopen(req_good)
        self.assertEqual(resp_good.status, 200)

        # Captura cookie de sessão
        set_cookie = resp_good.headers.get("Set-Cookie", "")
        self.assertIn(SESSION_COOKIE_NAME, set_cookie)
        cookie_val = set_cookie.split(";")[0]

        # 3. Acessa dashboard com cookie
        req_dash = urllib.request.Request(f"http://127.0.0.1:{self.port}/", headers={"Cookie": cookie_val})
        resp_dash = urllib.request.urlopen(req_dash)
        self.assertEqual(resp_dash.status, 200)
        html = resp_dash.read().decode("utf-8")
        self.assertIn("Bot 99Freelas", html)

        # 4. Acessa API com cookie
        req_api = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/metrics", headers={"Cookie": cookie_val})
        resp_api = urllib.request.urlopen(req_api)
        self.assertEqual(resp_api.status, 200)
        data = json.loads(resp_api.read().decode("utf-8"))
        self.assertIn("proposals_sent_count", data)


if __name__ == "__main__":
    unittest.main()
