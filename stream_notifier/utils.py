from typing import MutableMapping


def flatten_dict(input: dict, *keys):
    for key in keys:
        value = input.pop(key)
        if isinstance(value, MutableMapping):
            for k, v in value.items():
                input[f"{key}_{k}"] = v
    return input
