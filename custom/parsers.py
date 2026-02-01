import os
from pathlib import Path
from custom.log_util import log_msg
from custom.control_functions import exit_script

def parse_env_file(env_file_path: Path):
    if os.path.isfile(env_file_path):
        for line in env_file_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key, value)
    else:
        log_msg("ERROR: Could not find .env file. It should be placed in the directory the script is being executed from.", "red")
        exit_script(1, True)