import uuid
from pathlib import Path

from app.config import settings


class LocalFileStorage:
    def __init__(self):
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_content: bytes, original_filename: str) -> tuple[str, int]:
        ext = Path(original_filename).suffix
        stored_name = f"{uuid.uuid4()}{ext}"
        file_path = self.base_path / stored_name
        file_path.write_bytes(file_content)
        return str(file_path), len(file_content)

    async def delete(self, file_path: str):
        path = Path(file_path)
        if path.exists():
            path.unlink()


def get_storage():
    return LocalFileStorage()
