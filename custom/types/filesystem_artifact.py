from dataclasses import dataclass
from typing import Union, Any
from json import dumps
from datetime import datetime
from pathlib import Path
from .path_like import PathLike

@dataclass
class FilesystemArtifact:
    path: PathLike
    name: str = ""
    created: Union[str, datetime] = "unknown"
    modified: Union[str, datetime] = "unknown"
    obtained_at: datetime = datetime.now()

    def to_dict(self) -> dict[str, str]:
        str_dict: dict[str, Any] = {
            "path": str(self.path),
            "name": self.name,
            "created": str(self.created),
            "modified": str(self.modified),
            "obtained_at": str(self.obtained_at)
        }
        return str_dict

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        if not self.path.exists():
            raise FileNotFoundError(f"Path '{str(self.path)}' does not exist")
        self.name = self.path.stem
        self.created = datetime.fromtimestamp(self.path.stat().st_ctime)
        self.modified = datetime.fromtimestamp(self.path.stat().st_mtime)

    def __str__(self) -> str:
        return dumps(self.to_dict(), indent = 2)