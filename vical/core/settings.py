# vical/core/settings.py
from dataclasses import dataclass

@dataclass
class Settings:
    dim_when_completed: bool = True
    week_start: int = 6  # 6 = Sunday
    debug: bool = False
    view = 'monthly'