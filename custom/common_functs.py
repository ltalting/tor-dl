def dict_values_to_keys(dictionary: dict) -> dict:
    return {v: k if isinstance(v, str) else v for k, v in dictionary.items()}