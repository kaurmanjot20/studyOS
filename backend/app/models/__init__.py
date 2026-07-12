"""ORM models.

Import every model here so that `Base.metadata` is fully populated for Alembic
autogenerate and for `create_all` in tests. Concrete models are added per phase.
"""

from app.db.base import Base  # noqa: F401
from app.models.chat import ChatSession, Message  # noqa: F401
from app.models.document import Chunk, Document, DocumentStatus  # noqa: F401
from app.models.interview import InterviewSession  # noqa: F401
from app.models.memory import Memory, MemoryKind  # noqa: F401
from app.models.provider_settings import ProviderSettings  # noqa: F401
from app.models.study_artifact import StudyArtifact  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401

__all__ = [
    "Base",
    "Workspace",
    "ProviderSettings",
    "Document",
    "Chunk",
    "DocumentStatus",
    "ChatSession",
    "Message",
    "Memory",
    "MemoryKind",
    "InterviewSession",
    "StudyArtifact",
]
