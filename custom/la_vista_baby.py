from typing import Optional

def check_code(exit_code: Optional[int]) -> bool:
    return isinstance(exit_code, int) and exit >= 0

def exit_script_with_code(exit_code: int = 0):
    if check_code(exit_code):
        exit(exit_code)
    else:
        raise ValueError(f"Invalid exit code: {exit_code}")