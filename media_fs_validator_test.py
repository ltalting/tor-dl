from pathlib import Path
from os import environ
from custom.filesystem_functions import print_path, get_path
from custom.parsers import parse_env_file
from custom.log_util import log_msg

# Read in ENV file. See .env.template for example
parse_env_file(Path(".env"))

# Load in env-defined paths and values
try:
    local_downloads_dir = Path(environ.get("LOCAL_DOWNLOADS_DIR")) # where to store downloaded and scanned torrents
    video_fs_dir = Path(environ.get("VIDEO_FS_DIR"))
    magnet_links_file = Path(environ.get("MAGNET_LINKS_FILE"))
    tor_dl_script_file = Path(environ.get("TOR_DL_SCRIPT_FILE"))
except Exception as e:
    log_msg("ERROR: " + str(e), "red", exit = 1)
dir_local_downloads = get_path(local_downloads_dir)
dir_video_fs = get_path(video_fs_dir)
file_magnet_links = get_path(magnet_links_file)
file_tor_dl = get_path(tor_dl_script_file)

#print_path(dir_local_downloads.path)
#print_path(dir_video_fs.path)
# print_path(file_magnet_links.path)
print_path(file_tor_dl.path)

# types:
#  movies
#  tvshows
#  ...
class Movie:
    name: str
    year: str

class TvShow:
    name: str
    start_year: str
    end_year: str

# check naming based on type
# movies = title [year]
# tvshows = title[yearto-year]
# ...

