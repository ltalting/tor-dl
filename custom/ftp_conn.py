
from pathlib import Path
import time
from ftplib import FTP
from custom.log_util import log_msg

# Connect via ftp
def connect_ftp(ftp_host: str, ftp_user: str, ftp_pass: str, ftp_conn_retries: int = 0, ftp_timeout: int = 0, retry_delay: int = 0, ftp: FTP = None):
    if ftp is not None:
        try:
            ftp.close()
        except Exception:
            pass
    for attempt in range(1, ftp_conn_retries + 1):
        try:
            log_msg(f"Attempt {attempt} to connect to FTP server...", "blue", 1)
            ftp = FTP(ftp_host, timeout=ftp_timeout)
            ftp.login(user = ftp_user, passwd = ftp_pass)
            ftp.set_pasv(True)
            log_msg("Connected and logged in successfully.", "green", 2)
            return ftp
        except Exception as e:
            log_msg(f"Connection attempt {attempt} failed: {e}", "yellow", 2)
            if attempt < ftp_conn_retries:
                log_msg(f"Retrying in {retry_delay} seconds...", "yellow", 2)
                time.sleep(retry_delay)
            else:
                log_msg(f"ERROR: Failed to connect after {ftp_conn_retries} attempts.", "red")
                return None

# Check if a given file is a directory or over FTP
def is_directory_ftp(ftp_conn: FTP, file_name: str):
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
def download_ftp_tree(ftp_conn: FTP, remote_path, local_path):
    # Ensure local path is present; make it if it is not
    local_path = Path(local_path)
    local_path.mkdir(parents=True, exist_ok=True)
    # List files at remote_path
    # Print error and return when error occurs (usually if remote_path is not a directory)
    try:
        remote_files = ftp_conn.nlst(remote_path)
    except Exception as e:
        log_msg(f"ERROR: Could not list {remote_path}: {e}", "red", 2)
        return None
    
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
                    ftp_conn.retrbinary(f'RETR {remote_file_path}', f.write)
                log_msg(f"Downloaded: {file_name}", "green", 3)
            except Exception as e:
                log_msg(f"ERROR: Failed to download {file_name}: {e}", "red", 3)
