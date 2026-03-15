import sys
from random import randint
from typing import Optional
from .la_vista_baby import exit_script_with_code, check_code
from .common_functs import dict_values_to_keys

# Log message method
def log_msg(message = "", color = None, indent = None, stream = "stdout", exit: Optional[int] = None, **kwargs):
    # Handle color only if color is specified
    if color:
        colors = {
            "black": 30,
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
        if color.lower() in colors.keys():
                message = f"\033[{colors[color]}m{message}\033[0m"
        # Print random colors for every character when "critical" color is passed
        elif color.lower() == "critical":
            c_message = ""
            code_colors = dict_values_to_keys(colors)
            rand_int = randint(92, 96)
            last_int = 0
            for c in message:
                while rand_int == last_int:
                    rand_int = randint(92, 96)
                rand_color = code_colors[rand_int]
                c_message += f"\033[{rand_color}m{c}\033[0m"
                last_int = rand_int
            message = c_message
        else:
            # Log warning if color not found
            log_msg("CRITICAL ERROR: Color did not exist.", "critical")
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
    
    if exit:
        if check_code(exit):
            exit_script_with_code(exit)
        else:
            log_msg(f"CRITICAL ERROR: Exit code '{exit}' is invalid.", "critical", exit = 1)
