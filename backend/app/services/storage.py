"""Local file storage for uploaded documents.

Files are stored under `<storage_dir>/<workspace_id>/<document_id><ext>`. In Docker this
directory is a mounted volume so uploads survive restarts. Swapping to object storage
later means changing only this module.
"""

from __future__ import annotations

import os
import uuid

from app.core.config import settings


def _workspace_dir(workspace_id: uuid.UUID) -> str:
    path = os.path.join(settings.storage_dir, str(workspace_id))
    os.makedirs(path, exist_ok=True)
    return path


def save_upload(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    filename: str,
    data: bytes,
) -> tuple[str, int]:
    ext = os.path.splitext(filename)[1].lower()
    path = os.path.join(_workspace_dir(workspace_id), f"{document_id}{ext}")
    with open(path, "wb") as fh:
        fh.write(data)
    return path, len(data)


def delete_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
