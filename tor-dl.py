import argparse
import os
from pathlib import Path
from shlex import quote
from subprocess import CalledProcessError

from custom.control_functions import exit_script, run_cmd
from custom.ftp_conn import connect_ftp, download_ftp_tree
from custom.log_util import log_msg
from custom.parsers import parse_env_file

# Keep track of whether VM is running or not
vm_running = False

# Accept arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interactive", action="store_true", help="Run interactively")
args = parser.parse_args()

parse_env_file(Path(".env"))

try:
    # Local paths
    vagrant_dir = Path(os.environ.get("VAGRANT_DIR")) # vagrant-managed/hypervised directory
    torrent_files_dir = Path(os.environ.get("TORRENT_FILES_DIR")) # path to .torrent files
    local_downloads_dir = Path(os.environ.get("LOCAL_DOWNLOADS_DIR")) # where to store downloaded and scanned torrents
    # Remote paths
    remote_data_path = str(os.environ.get("REMOTE_DATA_PATH")) # path to FTP directory - ftpuser must have permissions to use this folder
    ftp_user_remote_data_path = str(os.environ.get("FTP_USER_REMOTE_DATA_PATH")) # ftpuser starts in /data

    # Define FTP vars
    ftp_host = str(os.environ.get("FTP_HOST"))
    ftp_user = str(os.environ.get("FTP_USER")) # Needs permissions to remote_data_path
    ftp_pass = str(os.environ.get("FTP_PASS"))
    ftp_timeout = int(os.environ.get("FTP_TIMEOUT")) # Seconds
    ftp_conn_retries = int(os.environ.get("FTP_CONN_RETRIES"))
    retry_delay = int(os.environ.get("RETRY_DELAY")) # Seconds
except Exception as e:
    log_msg("ERROR: " + str(e), "red")
    exit_script(
        vagrant_dir = vagrant_dir,
        exit_code = 1,
        vm_running = vm_running,
        interactive = args.interactive
    )
log_msg(f"{vagrant_dir, torrent_files_dir, local_downloads_dir, remote_data_path, ftp_user_remote_data_path, ftp_host, ftp_user, ftp_pass, ftp_timeout}")
# Initialize ftp client var
ftp = None

# Interactive or non?
if args.interactive:
    name = input("Enter your name: ")
    log_msg(f"Enjoy the downloads, {name}.", "magenta")
else:
    log_msg("Non-interactive mode", "magenta")

log_msg("Starting VM...", "blue")

# Start the tor VM
run_cmd(cmd = ["vagrant", "up"], working_dir = vagrant_dir)

# If we made it here, VM is running
vm_running = True

log_msg("VM started and configured successfully.", "green")

# Get list of local .torrent files
local_torrent_file_paths = list(torrent_files_dir.glob("*.torrent"))
local_torrent_file_names = [path_object.name for path_object in local_torrent_file_paths]
# If no .torrent files, exit okay no delete
if not local_torrent_file_paths:
    log_msg(f"No .torrent files existed in directory '{torrent_files_dir}'. Assuming testing.", "yellow")
    exit_script(
        vagrant_dir = vagrant_dir,
        exit_code = 0,
        vm_running = vm_running,
        interactive = args.interactive
    )

vpn_port = False
if args.interactive:
    selection_pending = True
    # Ask until we get a "y" or an "n" in the response
    while selection_pending:
        log_msg("Do you want to continue with downloading the following?", "blue")
        for file_name in local_torrent_file_names:
            log_msg(f"  - {file_name}", "yellow")
        selection = input("Enter your answer (y/n): ").strip().lower()
        if "y" in selection:
            break
        elif "n" in selection:
            exit_script(
                vagrant_dir = vagrant_dir,
                exit_code = 0,
                vm_running = vm_running,
                interactive = args.interactive
            )
        else:
            log_msg(f"Invalid selection '{selection}'. Please try again or exit the script via Ctrl-C.", "yellow", 1)
    selection_pending = True
    # Ask until we get a "y" or an "n" in the response
    while selection_pending:
        selection = input("VPN Port: ").strip().lower()
        if len(selection) > 0:
            vpn_port = int(selection.strip())
            break
        else:
            vpn_port=""
            break

log_msg("Uploading torrent file(s) via FTP...", "blue")

# Connect to FTP
ftp = connect_ftp(
    ftp_host = ftp_host,
    ftp_user = ftp_user,
    ftp_pass = ftp_pass,
    ftp_conn_retries = ftp_conn_retries,
    ftp_timeout = ftp_timeout,
    retry_delay = retry_delay
)

# Exit script if FTP connection not returned
if ftp == None:
    exit_script(
        vagrant_dir = vagrant_dir,
        exit_code = 1,
        vm_running = vm_running,
        interactive = args.interactive
    )

# Ensure passive mode. Windows quirk.
ftp.set_pasv(True)

torrent_start_cmds=[]
# Loop through files
for local_tor_file_path in local_torrent_file_paths:
    with open(local_tor_file_path, "rb") as f:
        log_msg(f"Uploading {local_tor_file_path}...", "blue", 1)
        ftp.storbinary(f"STOR {local_tor_file_path.name}", f)
        # Need to tell transmission where the .torrent is
        # Remote /data folder + local filename = remote file path to FTP's torrent file
        remote_tor_file_path = quote(f"{remote_data_path}/{local_tor_file_path.name}")
        # Form the start commands for the torrents (next step) using above
        tor_start = [
            "vagrant",
            "ssh",
            "-c",
            f"sudo -u {ftp_user} transmission-cli -u 0 -w {remote_data_path} {remote_tor_file_path}"
        ]
        if vpn_port:
            tor_start = [
                "vagrant",
                "ssh",
                "-c",
                f"sudo -u {ftp_user} transmission-cli -p {vpn_port} -u 0 -w {remote_data_path} {remote_tor_file_path}"
            ]
        torrent_start_cmds.append(tor_start)
        log_msg(f"Uploaded {local_tor_file_path.name}.", "green", 2)

log_msg("All torrents moved successfully to VM via FTP.", "green")

counter = 1
for command in torrent_start_cmds:
    log_msg(f"Starting download {counter} of {len(torrent_start_cmds)}...", "blue")
    run_cmd(cmd = command, working_dir = vagrant_dir)
    log_msg("Download complete.", "green")
    counter += 1
    # Kill that transmission session
    log_msg("Killing transmission-cli process...", "blue")
    run_cmd(cmd = ["vagrant", "ssh", "-c", "sudo pkill -f transmission-cli"], working_dir = vagrant_dir)

log_msg("All downloads complete.", "green")

# Scan with ClamAV
log_msg("Scanning downloaded files with ClamAV...", "blue")

# nice -n 19 = lowest CPU priority
scan_cmd = [
    "vagrant", "ssh", "-c",
    f"sudo nice -n 19 clamscan -r -i {remote_data_path}"
]
try:
    run_cmd(cmd = scan_cmd, working_dir = vagrant_dir, exit_on_error = False)
    log_msg("All files passed virus scan.", "green")
except CalledProcessError:
    log_msg("VIRUS DETECTED! Aborting and destroying VM.", "red")
    exit_script(
        vagrant_dir = vagrant_dir,
        exit_code = 1,
        vm_running = vm_running,
        interactive = args.interactive
    )

# mkdir for downloads if dir does not exist
local_downloads_dir.mkdir(exist_ok=True)

# Retrieve files from VM to host
log_msg("Retrieving clean files from VM...", "blue")

# Re-connect to FTP, it is surely dead at this point. If not, it will be closed an reopened.
ftp = connect_ftp(
    ftp_host = ftp_host,
    ftp_user = ftp_user,
    ftp_pass = ftp_pass,
    ftp_conn_retries = ftp_conn_retries,
    ftp_timeout = ftp_timeout,
    retry_delay = retry_delay
)

# Exit script if FTP connection not returned
if ftp == None:
    exit_script(
        vagrant_dir = vagrant_dir,
        exit_code = 1,
        vm_running = vm_running,
        interactive = args.interactive
    )

# Start the recursive download from root
download_ftp_tree(ftp, ftp_user_remote_data_path, local_downloads_dir)

log_msg("All files retrieved successfully.", "green")

exit_script(
    vagrant_dir = vagrant_dir,
    exit_code = 0,
    vm_running = vm_running,
    interactive = args.interactive
)