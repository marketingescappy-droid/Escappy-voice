import sqlite3
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path

FORMATS = ("Carrusel", "Reel", "Historia", "Publicación")
STATUSES = ("Idea", "En preparación", "Programada", "Publicada")
MEMORY_TYPES = ("Instrucción", "Preferencia", "Corrección")

SCHEMA = """
CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    planned_date TEXT NOT NULL,
    format TEXT NOT NULL,
    status TEXT NOT NULL,
    notes TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ideas_by_date ON ideas(planned_date, id);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS messages_by_conversation ON messages(conversation_id, id);
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    content TEXT NOT NULL
);
"""


def required(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"Completa el campo «{label}».")
    return value


class Storage:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def save_idea(self, title: str, planned_date: date, format_: str, status: str,
                  notes: str, idea_id: int | None = None):
        if format_ not in FORMATS or status not in STATUSES:
            raise ValueError("Selecciona un formato y un estado válidos.")
        values = (required(title, "Título"), planned_date.isoformat(), format_, status, notes.strip())
        with self.connect() as connection:
            if idea_id is None:
                return connection.execute(
                    "INSERT INTO ideas(title, planned_date, format, status, notes) VALUES (?, ?, ?, ?, ?)",
                    values,
                ).lastrowid
            connection.execute(
                "UPDATE ideas SET title=?, planned_date=?, format=?, status=?, notes=? WHERE id=?",
                (*values, idea_id),
            )
        return idea_id

    def ideas(self, first: date, last: date):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM ideas WHERE planned_date BETWEEN ? AND ? ORDER BY planned_date, id",
                (first.isoformat(), last.isoformat()),
            ).fetchall()

    def create_conversation(self, title: str):
        with self.connect() as connection:
            return connection.execute(
                "INSERT INTO conversations(title) VALUES (?)", (required(title, "Nombre"),)
            ).lastrowid

    def conversations(self):
        with self.connect() as connection:
            return connection.execute("SELECT * FROM conversations ORDER BY id DESC").fetchall()

    def add_message(self, conversation_id: int, content: str, role: str = "user"):
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO messages(conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, required(content, "Mensaje")),
            )

    def save_reply(self, conversation_id: int, last_user_id: int, content: str) -> bool:
        """Append only if the exact user message is still the end of the thread."""
        with self.connect() as connection:
            result = connection.execute(
                """
                INSERT INTO messages(conversation_id, role, content)
                SELECT ?, 'assistant', ?
                WHERE EXISTS (
                    SELECT 1 FROM (
                        SELECT id, role FROM messages
                        WHERE conversation_id=? ORDER BY id DESC LIMIT 1
                    ) AS latest WHERE latest.id=? AND latest.role='user'
                )
                """,
                (conversation_id, required(content, "Respuesta"), conversation_id, last_user_id),
            )
            return result.rowcount == 1

    def messages(self, conversation_id: int):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (conversation_id,)
            ).fetchall()

    def save_memory(self, kind: str, content: str, memory_id: int | None = None):
        if kind not in MEMORY_TYPES:
            raise ValueError("Selecciona un tipo de memoria válido.")
        content = required(content, "Contenido")
        with self.connect() as connection:
            if memory_id is None:
                return connection.execute(
                    "INSERT INTO memory(kind, content) VALUES (?, ?)", (kind, content)
                ).lastrowid
            connection.execute(
                "UPDATE memory SET kind=?, content=? WHERE id=?", (kind, content, memory_id)
            )
        return memory_id

    def memory(self):
        with self.connect() as connection:
            return connection.execute("SELECT * FROM memory ORDER BY id DESC").fetchall()
