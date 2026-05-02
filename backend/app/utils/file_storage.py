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

    async def save_thumbnail(self, part_id: str, image_content: bytes) -> str:
        thumb_dir = self.base_path / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = thumb_dir / f"{part_id}.png"
        thumb_path.write_bytes(image_content)
        return str(thumb_path)


def get_storage():
    return LocalFileStorage()
