import sqlite3
import threading
from pathlib import Path

from app.schemas import TaskResponse

TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"
CREATE_TASKS_TABLE = (
    "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
    "description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, "
    "created_at TEXT NOT NULL)"
)
INSERT_SEED_TASK = (
    "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"
)
SEED_TASKS = (
    ("Refactor login", "Separar responsabilidades en frontend", "TODO", "student", "HIGH"),
    ("Review API", "Revisar seguridad de endpoints", "IN_PROGRESS", "student", "MEDIUM"),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
)


class TaskRepository:
    """Único lugar con acceso a SQLite.

    Las consultas con `owner` y los INSERT siguen concatenados tal como estaban en main.py:
    su parametrización es el hallazgo H-API-03, fuera del alcance aprobado.
    """

    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()

    def init_schema(self) -> None:
        with self._lock:
            self.connection.execute(CREATE_TASKS_TABLE)

    def seed_if_empty(self) -> None:
        with self._lock:
            total = self.connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
            if total > 0:
                return
            for seed_task in SEED_TASKS:
                self.connection.execute(INSERT_SEED_TASK, seed_task)
            self.connection.commit()

    def list_by_owner(self, owner: str) -> list[TaskResponse]:
        sql = "SELECT " + TASK_COLUMNS + " FROM tasks WHERE owner='" + owner + "' ORDER BY id"
        with self._lock:
            return [as_task(row) for row in self.connection.execute(sql).fetchall()]

    def insert(self, title: str, description: str, status: str, owner: str, priority: str) -> TaskResponse:
        sql = (
            "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('"
            + title + "','" + description + "','" + status + "','" + owner + "','" + priority
            + "',datetime('now'))"
        )
        with self._lock:
            cursor = self.connection.execute(sql)
            self.connection.commit()
            return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, task_id: int) -> TaskResponse:
        sql = "SELECT " + TASK_COLUMNS + " FROM tasks WHERE id=" + str(task_id)
        with self._lock:
            return as_task(self.connection.execute(sql).fetchone())

    def status_and_priority_by_owner(self, owner: str) -> list[tuple[str, str]]:
        sql = "SELECT status,priority FROM tasks WHERE owner='" + owner + "'"
        with self._lock:
            return [(row["status"], row["priority"]) for row in self.connection.execute(sql).fetchall()]

    def close(self) -> None:
        with self._lock:
            self.connection.close()


def as_task(row: sqlite3.Row) -> TaskResponse:
    return TaskResponse.model_validate(dict(row))
