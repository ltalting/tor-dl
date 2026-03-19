from typing import Union
from .file_metadata import FileMetadata
from .video_file_metadata import VideoFileMetadata

FileLike = Union[FileMetadata, VideoFileMetadata]