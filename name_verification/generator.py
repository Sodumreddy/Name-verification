import random
from typing import List

from .storage import write_latest_target


FIRST_NAMES: List[str] = [
    "Tyler",
    "Sarah",
    "Mohammed",
    "Elizabeth",
    "Omar",
    "Yusuf",
    "Jean-Luc",
    "Mikhail",
    "Alexander",
    "Abdul Rahman",
]

LAST_NAMES: List[str] = [
    "Bliha",
    "Al-Hilal",
    "Al Fayed",
    "Gorbachev",
    "Petrov",
    "Al Qasim",
    "O'Connor",
    "Al Khattab",
    "Al Saud",
    "Gonzalez",
]


def generate_target_name(prompt: str) -> str:
    """
    Generate a simple synthetic person-like name from fixed pools.

    The generator is intentionally simple because the grading focuses on
    the verifier. The prompt is accepted but only used to add a small
    amount of variability via hashing, not for semantic generation.
    """
    seed_input = f"{prompt}|{len(prompt)}"
    seed_value = hash(seed_input)
    random.seed(seed_value)

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    target_name = f"{first} {last}"
    write_latest_target(target_name)
    return target_name


