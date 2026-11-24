"""Testes do dashboard de métricas e quadro Kanban."""

import unittest
from bot_99freelas.dashboard.models import TaskStatus
from bot_99freelas.dashboard.kanban import kanban_manager
from bot_99freelas.dashboard.service import dashboard_service
from bot_99freelas.storage.db import db


class TestDashboard(unittest.TestCase):
    def setUp(self):
        # Limpa dados de teste
        db._data["tasks"] = []
        db._data["proposals"] = []
        db._save()

    def test_kanban_task_creation_and_movement(self):
        task = kanban_manager.create_task(
            project_id="proj-101",
            title="Integrar API de pagamento",
            description="Criar webhook",
        )
        self.assertEqual(task.status, TaskStatus.TODO)

        # Move para Em Andamento
        moved = kanban_manager.move_task(task.id, TaskStatus.IN_PROGRESS)
        self.assertTrue(moved)

        cols = kanban_manager.get_board_columns()
        self.assertEqual(len(cols[TaskStatus.IN_PROGRESS.value]), 1)
        self.assertEqual(cols[TaskStatus.IN_PROGRESS.value][0].id, task.id)

    def test_project_workflow_auto_init(self):
        tasks = kanban_manager.init_project_workflow("proj-202", "Bot de Planilhas")
        self.assertEqual(len(tasks), 3)
        self.assertIn("Alinhamento", tasks[0].title)
        self.assertIn("Desenvolvimento", tasks[1].title)
        self.assertIn("Entrega", tasks[2].title)

    def test_metrics_calculation(self):
        db._data["proposals"] = [
            {"id": 1, "project_id": "p1", "price": 300.0, "status": "accepted"},
            {"id": 2, "project_id": "p2", "price": 450.0, "status": "pending_approval"},
            {"id": 3, "project_id": "p3", "price": 250.0, "status": "sent"},
        ]
        db._save()

        metrics = dashboard_service.calculate_metrics()
        self.assertEqual(metrics.proposals_sent_count, 3)
        self.assertEqual(metrics.accepted_projects_count, 1)
        self.assertEqual(metrics.total_revenue_earned, 300.0)
        self.assertEqual(metrics.pipeline_value, 700.0)  # 450 + 250
        self.assertAlmostEqual(metrics.conversion_rate_percent, 33.3, places=1)

    def test_web_dashboard_template(self):
        from bot_99freelas.dashboard.web import HTML_TEMPLATE
        self.assertIn("Bot 99Freelas", HTML_TEMPLATE)
        self.assertIn("Faturamento Total", HTML_TEMPLATE)
        self.assertIn("Quadro de Execução", HTML_TEMPLATE)

    def test_dashboard_javascript_syntax(self):
        import re
        import shutil
        import subprocess
        from bot_99freelas.dashboard.templates import DASHBOARD_HTML_TEMPLATE

        if not shutil.which("node"):
            return

        scripts = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", DASHBOARD_HTML_TEMPLATE, re.DOTALL)
        inline_scripts = [s for s in scripts if s.strip()]
        for idx, s in enumerate(inline_scripts):
            res = subprocess.run(["node", "--check"], input=s, text=True, capture_output=True)
            self.assertEqual(res.returncode, 0, f"JS syntax error in script #{idx}: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
