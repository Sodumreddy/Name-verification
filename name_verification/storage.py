from pathlib import Path
from typing import Optional


LATEST_TARGET_PATH = Path(__file__).with_name("latest_target.txt")


def write_latest_target(name: str) -> None:
    """
    Persist the latest generated target name so the verifier can treat
    the generator as a black box and only read this string.
    """
    LATEST_TARGET_PATH.write_text(name.strip(), encoding="utf-8")


def read_latest_target() -> Optional[str]:
    """
    Read the latest generated target name, if it exists.
    """
    if not LATEST_TARGET_PATH.exists():
        return None
    text = LATEST_TARGET_PATH.read_text(encoding="utf-8").strip()
    return text or None


