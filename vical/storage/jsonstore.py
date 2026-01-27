# jsonstore.py - JSON persistence for vical
# This file is part of vical.
# License: MIT (see LICENSE)

import os
import json
from typing import List

from vical.core.subcalendar import Subcalendar

DATA_DIR = os.path.expanduser("~/.local/share/vical")
DATA_FILE = os.path.join(DATA_DIR, "subcalendars.json")

def save_subcalendars(
    subcalendars: List[Subcalendar],
    filepath: str = DATA_FILE,
) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            [sc.to_dict() for sc in subcalendars],
            f,
            indent=2,
            ensure_ascii=False,
        )

def load_subcalendars(filepath: str = DATA_FILE) -> List[Subcalendar]:
    if not os.path.exists(filepath):
        default = Subcalendar("default")
        save_subcalendars([default], filepath)
        return [default]

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Invalid vical data format: expected a list")

    return [Subcalendar.from_dict(d) for d in data]
