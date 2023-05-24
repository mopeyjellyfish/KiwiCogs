from typing import Tuple


def parse_target(target: str) -> Tuple[str, str]:
    """Parses a target path, providing the first item & remaining path

    :param target: The target for the transition
    :returns: Tuple[str, str]
    """
    target_state = None
    remainder = None
    while not target_state:
        values = target.split(".", maxsplit=1)
        target_state = values[0]
        target = remainder = values[-1]

    return target_state, remainder
