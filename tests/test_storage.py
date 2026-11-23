"""Testes do banco de dados SQLite local e controle de conexões."""

import unittest
import tempfile
from pathlib import Path
from bot_99freelas.storage.db import Database


class TestDatabase(unittest.TestCase):
    def test_database_operations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Database(file_path=Path(tmpdir) / "test.json")

            self.assertFalse(test_db.is_project_seen("p1"))

            test_db.record_project(
                project_id="p1",
                url="https://99freelas.com.br/project/p1",
                title="Projeto Teste",
                budget_min=200.0,
                budget_max=400.0,
                proposals_count=2,
                client_name="Cliente A",
                score=90.0,
                status="approved",
                reasons="Aprovado com sucesso",
            )

            self.assertTrue(test_db.is_project_seen("p1"))

            prop_id = test_db.record_proposal(
                project_id="p1",
                price=250.0,
                delivery_days=2,
                proposal_text="Proposta teste",
            )
            self.assertGreater(prop_id, 0)

            # Controle de conexões
            self.assertEqual(test_db.get_today_connections_used(), 0)
            used = test_db.increment_today_connections()
            self.assertEqual(used, 1)
            self.assertTrue(test_db.can_send_proposal_today())


if __name__ == "__main__":
    unittest.main()
