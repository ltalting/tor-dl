from typing import Any

def dict_values_to_keys(dictionary: dict) -> dict:
    return {v: k if isinstance(v, str) else v for k, v in dictionary.items()}

def any_to_str(any: Any) -> str:
    return str(any)