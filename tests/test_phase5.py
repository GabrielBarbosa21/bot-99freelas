"""Testes das funcionalidades da Fase 5 (Cards 5.1, 5.2, 5.3)."""

import unittest
from unittest.mock import patch
from bot_99freelas.crawler.controller import MonitorController
from bot_99freelas.crawler.session import FreelasSession
from bot_99freelas.crawler.monitor import LOGS_DIR, LOG_FILE


class TestPhase5(unittest.TestCase):
    def test_session_health_verification(self):
        session = FreelasSession()
        
        # Teste 1: Sem cookies
        with patch.object(session, "load_cookies", return_value={}):
            health = session.verify_session_health()
            self.assertFalse(health["valid"])
            self.assertFalse(health["has_cookies"])
            self.assertEqual(health["cookie_count"], 0)

        # Teste 2: Com cookies válidos
        with patch.object(session, "load_cookies", return_value={"JSESSIONID": "xyz123", "kmlicn": "hashabc"}):
            health = session.verify_session_health()
            self.assertTrue(health["valid"])
            self.assertTrue(health["has_cookies"])
            self.assertEqual(health["cookie_count"], 2)

    def test_monitor_controller_logs_and_status(self):
        controller = MonitorController(max_log_history=10)
        self.assertFalse(controller.is_running)

        controller.add_log("Teste de log 1")
        controller.add_log("Teste de log 2")
        logs = controller.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn("Teste de log 1", logs[0])
        self.assertIn("Teste de log 2", logs[1])

        status = controller.get_status()
        self.assertIn("active", status)
        self.assertIn("cycles_completed", status)
        self.assertIn("session_valid", status)

        controller.clear_logs()
        self.assertEqual(len(controller.get_logs()), 0)

    def test_logs_directory_and_file_setup(self):
        self.assertTrue(str(LOG_FILE).endswith("bot_99freelas.log"))


if __name__ == "__main__":
    unittest.main()
