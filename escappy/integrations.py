from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class CreativeNote:
    kind: str
    content: str


class ChatProvider(Protocol):
    def reply(self, history: Sequence[ChatMessage], memory: Sequence[CreativeNote]) -> str:
        """Generate a reply using the conversation and creative memory."""


PLANNED_INTEGRATIONS = {
    "Canva": "Diseños y recursos visuales.",
    "Google Drive": "Archivos y materiales de referencia.",
    "ClickUp": "Seguimiento de tareas editoriales.",
    "Higgsfield": "Flujo de producción audiovisual.",
}
