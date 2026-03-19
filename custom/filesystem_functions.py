import re
from pathlib import Path
from typing import Optional, Callable, Union
from .log_util import log_msg
from .types.file_metadata import FileMetadata
from .types.directory_metadata import DirectoryMetadata
from .types.path_like import PathLike
from .types.file_like import FileLike
from .types.video_file_metadata import VideoFileMetadata

text_extensions = {".txt", ".py", ".log"}
video_extensions = {".mkv", ".avi", ".mp4"}

# Check existence/return target type flag
def _exists(target: PathLike) -> Optional[dict[str, PathLike]]:
    path = Path(target)
    if path.exists():
         return {"target": path, "target_type_flag": "d"} if path.is_dir() else {"target": path, "target_type_flag": "f"}
    else:
        return None

def count_file_lines(file_path: PathLike):
    file = get_file(file_path)
    with open(file.path, 'r') as f:
        line_count = sum(1 for line in f)
    return line_count

# Get file metadata
def get_file(file_path: PathLike) -> FileLike:
    file = FileMetadata(file_path)
    if file.extension in video_extensions:
        file.__class__ = VideoFileMetadata
    return file

# Get directory metadata
def get_directory(dir_path: PathLike) -> DirectoryMetadata:
    return DirectoryMetadata(dir_path)

# Get file or directory metadata
def get_path(target: PathLike) -> Union[FileLike, DirectoryMetadata]:
    path = _exists(target)
    if not path:
        raise FileNotFoundError(f"Path does not exist: {target}")
    getters: dict[str, Callable] = {
        "f": get_file,
        "d": get_directory
    }
    return getters[path["target_type_flag"]](path["target"])

# Print file lines and contents to cli
def print_file(file_path: PathLike) -> None:
    file = get_file(file_path)
    if file.extension in text_extensions:
        line_count = count_file_lines(file.path)
        pad_width = len(str(line_count)) + 2
        with file.path.open("r", encoding = "utf-8", errors = "replace") as opened_file:
            for line_number, line in enumerate(opened_file, start = 1):
                padded_line_number = str(line_number).ljust(pad_width, ' ')
                log_msg(f"{padded_line_number}{line.rstrip()}")
    elif file.extension in video_extensions:
        log_msg("VIDEO FILE DETECTED: print_file() not implemented.", "yellow")
    else:
        log_msg(f"ERROR: File with extension {file.extension} is not printable", "red", 1)

# Print dir files and subdirs
def print_directory(dir_path: PathLike, indent: int = 0) -> None:
    prefix = " " * indent

    dir = get_directory(dir_path)

    dirs = sorted([p for p in dir.sub_directories if p.is_dir()], key = lambda p: p.name.lower())
    files = sorted([p for p in dir.files if p.is_file()], key = lambda p: p.name.lower())

    for d in dirs:
        dir = DirectoryMetadata(d)
        log_msg(f"{prefix}{dir.name} (total: {dir.contained_bytes} bytes)/")
        print_directory(dir.path, indent + 2)

    for f in files:
        file = FileMetadata(f)
        log_msg(f"{prefix}{file.name} ({file.size_in_bytes} bytes)")

def print_path(target: PathLike) -> None:
    path = _exists(target)
    if not path:
        raise FileNotFoundError(f"Path does not exist: {target}")
    printers: dict[str, Callable] = {
        "f": print_file,
        "d": print_directory
    }
    return printers[path["target_type_flag"]](path["target"])