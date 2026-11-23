"""Gerenciador do quadro Kanban interativo para projetos aceitos (Card 4.2)."""

import uuid
from typing import List, Dict
from bot_99freelas.dashboard.models import KanbanTask, TaskStatus
from bot_99freelas.storage.db import db


class KanbanManager:
    """Gerencia as colunas e tarefas dos projetos aceitos."""

    def __init__(self):
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if "tasks" not in db._data:
            db._data["tasks"] = []
            db._save()

    def create_task(self, project_id: str, title: str, description: str = "") -> KanbanTask:
        """Cria uma nova tarefa no Kanban."""
        self._ensure_storage()
        task = KanbanTask(
            id=f"tsk-{uuid.uuid4().hex[:6]}",
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.TODO,
        )
        db._data["tasks"].append(task.model_dump())
        db._save()
        return task

    def init_project_workflow(self, project_id: str, project_title: str) -> List[KanbanTask]:
        """Cria automaticamente as 3 tarefas padrão de execução ágil quando o projeto é aceito."""
        t1 = self.create_task(
            project_id=project_id,
            title=f"Alinhamento & Credenciais: {project_title}",
            description="Validar acessos, repositório e requisitos específicos no chat.",
        )
        t2 = self.create_task(
            project_id=project_id,
            title=f"Desenvolvimento & Testes: {project_title}",
            description="Implementação do escopo com testes automatizados.",
        )
        t3 = self.create_task(
            project_id=project_id,
            title=f"Entrega & Homologação: {project_title}",
            description="Homologação final junto ao cliente e início dos 7 dias de garantia.",
        )
        return [t1, t2, t3]

    def move_task(self, task_id: str, new_status: TaskStatus) -> bool:
        """Move uma tarefa entre as colunas do Kanban."""
        self._ensure_storage()
        for t in db._data["tasks"]:
            if t["id"] == task_id:
                t["status"] = new_status.value
                db._save()
                return True
        return False

    def get_board_columns(self) -> Dict[str, List[KanbanTask]]:
        """Retorna as tarefas agrupadas por coluna do Kanban."""
        self._ensure_storage()
        columns: Dict[str, List[KanbanTask]] = {
            TaskStatus.TODO.value: [],
            TaskStatus.IN_PROGRESS.value: [],
            TaskStatus.REVIEW.value: [],
            TaskStatus.DONE.value: [],
        }
        for item in db._data.get("tasks", []):
            task = KanbanTask(**item)
            if task.status.value in columns:
                columns[task.status.value].append(task)
        return columns


kanban_manager = KanbanManager()
