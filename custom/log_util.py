import sys

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
