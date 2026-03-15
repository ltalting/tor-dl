from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from json import dumps
from .filesystem_artifact import FilesystemArtifact


@dataclass
class DirectoryMetadata(FilesystemArtifact):
    contained_bytes: Optional[int] = None
    sub_directories: list[Path] = field(default_factory = list[Path])
    files: list[Path] = field(default_factory = list[Path])

    def to_dict(self) -> dict[str, Any]:
        merged_dict = super().to_dict()
        merged_dict["contained_bytes"] = self.contained_bytes
        merged_dict["sub_directories"] = [str(x) for x in self.sub_directories]
        merged_dict["files"] = [str(x) for x in self.files]
        return merged_dict

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.path.is_dir():
            raise ValueError(f"Not a directory: {str(self.path)}")
        # Directory size (recursive)
        self.contained_bytes = sum(
            f.stat().st_size for f in self.path.rglob("*") if f.is_file()
        )
        # sub_dirs
        sub_dirs = [Path(x) for x in self.path.iterdir() if x.is_dir()]
        self.sub_directories = sub_dirs if sub_dirs is not None else []
        # files
        files = [Path(x) for x in self.path.iterdir() if x.is_file()]
        self.files = files if files is not None else []
    
    def __str__(self) -> str:
        return dumps(self.to_dict(), indent = 2)