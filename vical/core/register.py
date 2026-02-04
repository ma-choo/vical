# editor.py - Registers.
# This file is part of vical.
# License: MIT (see LICENSE)

from dataclasses import dataclass
from typing import Literal


class Register:
    def __init__(self):
        # unnamed register and numbered registers 1–9
        self.named = {
            '"': None,
            **{str(i): None for i in range(1, 10)}
        }

    def set(self, item, use_numbered=True):
        """
        Store a CalendarItem in the registers.
        use_numbered: if True, rotate numbered registers (1–9)
        """
        payload = item.to_register()
        self.named['"'] = payload  # store the payload, not the raw item

        if use_numbered:
            # Shift registers 1–8 up
            for i in range(9, 1, -1):
                self.named[str(i)] = self.named.get(str(i - 1))
            self.named['1'] = payload


    def get(self, key='"'):
        """Retrieve a CalendarItem by register key (default is unnamed)."""
        return self.named.get(key)

    def clear(self, key='"'):
        self.named[key] = None


@dataclass
class RegisterPayload:
    kind: Literal["task", "event"]
    data: dict