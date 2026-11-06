from pathlib import Path
from uuid import uuid4

from app.core.errors import DomainError


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write_docx(self, writer) -> str:
        key = f'{uuid4()}.docx'
        writer(self.root / key)
        return key

    def path(self, key: str) -> Path:
        resolved = (self.root / key).resolve()
        if resolved.parent != self.root or not resolved.is_file():
            raise DomainError('NOT_FOUND', 'Không tìm thấy tệp.', 404)
        return resolved
