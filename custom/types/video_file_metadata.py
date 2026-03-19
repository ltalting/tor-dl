from typing import Optional, Any
from dataclasses import dataclass
from json import dumps
from .file_metadata import FileMetadata

@dataclass
class VideoFileMetadata(FileMetadata):
    duration: Optional[float] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    framerate: Optional[float] = None
    audio_codec: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        merged_dict = super().to_dict()
        merged_dict["duration"] = self.duration
        merged_dict["video_codec"] = self.codec
        merged_dict["width"] = self.width
        merged_dict["height"] = self.height
        merged_dict["framerate"] = self.framerate
        merged_dict["audio_codec"] = self.audio_codec
        merged_dict["bitrate"] = self.bitrate
        return merged_dict

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.path.is_file():
            raise ValueError(f"Not a file: {str(self.path)}")
        # File extension
        self.extension = self.path.suffix
        # File size
        self.size_in_bytes = self.path.stat().st_size
    
    def __str__(self) -> str:
        return dumps(self.to_dict(), indent = 2)