from typing import Optional, Any
from dataclasses import dataclass
from json import dumps
from .filesystem_artifact import FilesystemArtifact

@dataclass
class FileMetadata(FilesystemArtifact):
    extension: str = "unknown"
    size_in_bytes: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        merged_dict = super().to_dict()
        merged_dict["extension"] = self.extension
        merged_dict["size_in_bytes"] = self.size_in_bytes
        return merged_dict

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.path.is_file():
            raise ValueError(f"Not a file: {str(self.path)}")
        # File extension
        if self.extension == "unknown":
            self.extension = self.path.suffix
        # File size
        self.size_in_bytes = self.path.stat().st_size
    
    def __str__(self) -> str:
        return dumps(self.to_dict(), indent = 2)