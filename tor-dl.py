import argparse
import time
import sys
import os
from shlex import quote
from subprocess import Popen as p_open, PIPE, STDOUT, CalledProcessError
from pathlib import Path
from ftplib import FTP

# Keep track of whether VM is running or not
vm_running = False

# Accept arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interactive", action="store_true", help="Run interactively")
args = parser.parse_args()

# Log message method
def log_msg(message = "", color = None, indent = None, stream = "stdout", **kwargs):
    # Handle color only if color is specified
    if color:
        colors = {
            "gray": 90,
            "red": 91,
            "green": 92,
            "yellow": 93,
            "blue": 94,
            "magenta": 95,
            "cyan": 96,
            "white": 97
        }
        # Update message with color if color specified
        if color in colors.keys():
            message = f"\033[{colors[color]}m{message}\033[0m"
        else:
            # Log warning if color not found
            log_msg("Color did not exist.", "yellow")
    indentation=""
    # Handle indentation only if indentation is specified
    # Indentation is specified per-level i.e. 1 = 2 space, 2 = 4 space, 3 = 6 space, etc...
    if indent:
        indentation = "  " * indent
    message = indentation + message
    # Print to declared stream
    if stream == "stdout":
        print(message, file = sys.stdout, **kwargs)
    else:
        print(message, file = sys.stderr, **kwargs)

# Exit routine. Will deprov a running vm if deprov_vm is not False
def exit_script(exit_code = 0, deprov_vm = None):
    log_msg("Exiting script...", "blue")
    global args, vm_running
    if vm_running:
        # Interactive mode will ask for this
        if args.interactive:
            selection_pending = True
            # Ask until we get a "y" or an "n" in the response
            while selection_pending:
                selection = input("Destroy VM? (y/n): ").strip().lower()
                if "y" in selection:
                    deprov_vm = True
                    selection_pending = False
                elif "n" in selection:
                    deprov_vm = False
                    selection_pending = False
                else:
                    log_msg(f"Invalid selection '{selection}'. Please try again or exit the script via Ctrl-C.", "yellow", 1)
        # Decide if kill_vm
        if deprov_vm:
            kill_vm()
        else:
            log_msg("Script will not destroy VM.", "yellow", 1)
    else:
        log_msg("VM is not running to be destroyed.", "yellow", 1)
        if args.interactive:
            log_msg("Press Enter key to close...", "blue")
            input()
    log_msg("Smell ya later!", "cyan")
    exit(exit_code)

def load_env_file(env_file_path: Path):
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

load_env_file(Path(".env"))

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
    exit_script(1)
log_msg(f"{vagrant_dir, torrent_files_dir, local_downloads_dir, remote_data_path, ftp_user_remote_data_path, ftp_host, ftp_user, ftp_pass, ftp_timeout}")
# Initialize ftp client var
ftp = None

# Execute shell commands safely. This is used to execute Vagrant commands on the host.
# https://docs.python.org/3/library/subprocess.html#subprocess.run
def run_cmd(cmd, working_dir = None, timeout = None, exit_on_error = True):
    try:
        # Initialize return code None
        return_code = None
        # Start the command
        result = p_open(args = cmd, cwd = working_dir, stdout = PIPE, stderr = STDOUT, text = True)
        # Handle timeout if specified
        if timeout is not None and isinstance(timeout, (int, float)):
            start_time = time.time()
            for line in result.stdout:
                # Break when seeding is reached for tor DL commands
                if line.startswith("Seeding, uploading"):
                    result.kill()
                    return_code = 0
                    break
                # Check timeout. Kill and fail if reached.
                if time.time() - start_time > timeout:
                    result.kill()
                    raise TimeoutError("Command timed out.")
                log_msg(line, "gray", indent = 1, end = "")
        # No timeout
        else:
            for line in result.stdout:
                # Break when seeding is reached for tor DL commands
                if line.startswith("Seeding, uploading"):
                    result.kill()
                    return_code = 0
                    break
                # Only log progress messages
                if line.startswith("Progress:"):
                    log_msg(line, "green", indent = 1, end = "")
                    continue
                log_msg(line, "gray", indent = 1, end = "")
        result.wait()
        # If manual return_code was set
        if return_code is not None:
            if return_code != 0:
                raise CalledProcessError(return_code, cmd)
        elif result.returncode != 0:
            raise CalledProcessError(result.returncode, cmd)
        # Success
        log_msg("Command completed successfully.", "green", indent = 1)
        return result
    except TimeoutError as e:
        log_msg("ERROR: " + str(e), "red", indent = 1)
        if exit_on_error:
            exit_script(1)
        else:
            raise
    except CalledProcessError as e:
        log_msg(f"ERROR: Command failed: ({e.cmd}).", "red", indent = 1)
        if exit_on_error:
            exit_script(1)
        else:
            raise

# Kill VM method
def kill_vm():
    # Use vm_running variable from above context
    global vm_running
    # Destroy only if vm_running
    if vm_running:
        log_msg("Destroying VM...", "blue")
        # Destroy VM
        run_cmd(cmd = ["vagrant", "destroy", "-f"], working_dir = vagrant_dir)
        # Update global vm_running var
        vm_running = False
        log_msg("VM destroyed.", "green")
    # Otherwise, just print
    else:
        log_msg("VM was not running.", "green")

def connect_ftp():
    global ftp
    if ftp is not None:
        try:
            ftp.close()
        except Exception:
            pass
    for attempt in range(1, ftp_conn_retries + 1):
        try:
            log_msg(f"Attempt {attempt} to connect to FTP server...", "blue", 1)
            ftp = FTP(ftp_host, timeout=ftp_timeout)
            ftp.login(user=ftp_user, passwd=ftp_pass)
            ftp.set_pasv(True)
            log_msg("Connected and logged in successfully.", "green", 2)
            return
        except Exception as e:
            log_msg(f"Connection attempt {attempt} failed: {e}", "yellow", 2)
            if attempt < ftp_conn_retries:
                log_msg(f"Retrying in {retry_delay} seconds...", "yellow", 2)
                time.sleep(retry_delay)
            else:
                log_msg(f"ERROR: Failed to connect after {ftp_conn_retries} attempts.", "red")
                exit_script(1)

# Check if a given file is a directory or over FTP
def is_directory_ftp(ftp_conn, file_name):
    try:
        # Save current dir to switch back to
        current_working_dir = ftp_conn.pwd()
        # Try to change working dir to specified file. If it is a directory, this command will succeed
        ftp_conn.cwd(file_name)
        # Switch context back to where it started if file is a directory
        ftp_conn.cwd(current_working_dir)
        return True
    except:
        return False

# Recurse through the tree of files located at remote_path and download the structure into local_path via FTP
# Ignore '.', '..', 'lost+found', and the file we STOR to ensure FTP readiness, '.ftp_ready'
def download_ftp_tree(ftp_conn, remote_path, local_path):
    # Ensure local path is present; make it if it is not
    local_path = Path(local_path)
    local_path.mkdir(parents=True, exist_ok=True)
    # List files at remote_path
    # Print error and return when error occurs (usually if remote_path is not a directory)
    try:
        remote_files = ftp_conn.nlst(remote_path)
    except Exception as e:
        log_msg(f"ERROR: Could not list {remote_path}: {e}", "red", 2)
        exit_script(0, False)
    
    for remote_file_path in remote_files:
        # Get just the filename from the path
        file_name = remote_file_path.split('/')[-1]
        
        # Skip special files
        if file_name in ['.', '..', 'lost+found', '.ftp_ready']:
            continue
        
        # Skip torrent files
        if file_name.endswith('.torrent'):
            continue
        
        # Append to path object. Division operator is overloaded to append strings/paths to Path objects
        # https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.__truediv__
        local_file_path = local_path / file_name
        
        # Check if it's a directory
        if is_directory_ftp(ftp_conn, remote_file_path):
            log_msg(f"Entering directory: {file_name}", "blue", 1)
            download_ftp_tree(ftp_conn, remote_file_path, local_file_path)
        else:
            # Otherwise, it must be a file, download it
            log_msg(f"Downloading: {file_name}", "blue", 2)
            try:
                # Open write buffer to local file path and write the FTP RETR to it
                with open(local_file_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {remote_file_path}', f.write)
                log_msg(f"Downloaded: {file_name}", "green", 3)
            except Exception as e:
                log_msg(f"ERROR: Failed to download {file_name}: {e}", "red", 3)

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
log_msg("Uploading torrent file(s) via FTP...", "blue")

# Connect to FTP
connect_ftp()

# Ensure passive mode. Windows quirk.
ftp.set_pasv(True)

# Get list of local .torrent files
local_torrent_files = list(torrent_files_dir.glob("*.torrent"))

# If no .torrent files, exit okay no delete
if not local_torrent_files:
    log_msg(f"No .torrent files existed in directory '{torrent_files_dir}'. Assuming testing.", "yellow")
    exit_script(0, False)

torrent_start_cmds=[]
# Loop through files
for local_tor_file_path in local_torrent_files:
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
    exit_script(1)

# mkdir for downloads if dir does not exist
local_downloads_dir.mkdir(exist_ok=True)

# Retrieve files from VM to host
log_msg("Retrieving clean files from VM...", "blue")

connect_ftp()
# Start the recursive download from root
download_ftp_tree(ftp, ftp_user_remote_data_path, local_downloads_dir)

log_msg("All files retrieved successfully.", "green")

exit_script(0, False)