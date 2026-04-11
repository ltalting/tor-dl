from typing import Optional, Any
from dataclasses import dataclass
from json import dumps
import winshell

from .file_metadata import FileMetadata


@dataclass
class LinkFileMetadata(FileMetadata):
    target_path: Optional[str] = None
    working_directory: Optional[str] = None
    arguments: Optional[str] = None
    description: Optional[str] = None
    icon_location: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        merged_dict = super().to_dict()
        merged_dict["target_path"] = self.target_path
        merged_dict["working_directory"] = self.working_directory
        merged_dict["arguments"] = self.arguments
        merged_dict["description"] = self.description
        merged_dict["icon_location"] = self.icon_location
        return merged_dict

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.path.is_file():
            raise ValueError(f"Not a file: {self.path}")

        if self.path.suffix.lower() != ".lnk":
            raise ValueError(f"Not a Windows shortcut (.lnk): {self.path}")

        # File extension
        self.extension = self.path.suffix

        # File size
        self.size_in_bytes = self.path.stat().st_size

        # Resolve shortcut
        shortcut = winshell.shortcut(str(self.path))

        self.target_path = shortcut.path
        self.working_directory = shortcut.working_directory
        self.arguments = shortcut.arguments
        self.description = shortcut.description
        self.icon_location = shortcut.icon_location

    def __str__(self) -> str:
        return dumps(self.to_dict(), indent=2)