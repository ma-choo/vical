# This file is part of vical.
# License: MIT (see LICENSE)

"""
Settings.
"""

from dataclasses import dataclass
from enum import Enum, auto

class View(Enum):
    MONTH = auto()
    WEEK = auto()

@dataclass
class Settings:
    view = View.MONTH
    date_format = "mdy"
    dim_when_completed: bool = True
    week_start: int = 6  # 6 = Sunday
    debug: bool = False
    max_history = 50