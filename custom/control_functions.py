import time
from subprocess import CalledProcessError, PIPE, Popen as p_open, STDOUT
from pathlib import Path
from custom.log_util import log_msg

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
def kill_vm(vagrant_dir: Path, vm_running: bool = True):
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


# Exit routine. Will deprov a running vm if deprov_vm is not False. Assumes VM is running if not specified.
def exit_script(vagrant_dir: Path, exit_code: int = 0, deprov_vm: bool = False, vm_running: bool = True, interactive: bool = False):
    log_msg("Exiting script...", "blue")
    if vm_running:
        # Interactive mode will ask for this
        if interactive:
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
            kill_vm(vagrant_dir)
        else:
            log_msg("Script will not destroy VM.", "yellow", 1)
    else:
        log_msg("VM is not running to be destroyed.", "yellow", 1)
        if interactive:
            log_msg("Press Enter key to close...", "blue")
            input()
    log_msg("Smell ya later!", "cyan")
    exit(exit_code)
