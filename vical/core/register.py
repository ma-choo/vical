# editor.py - Registers.
# This file is part of vical.
# License: MIT (see LICENSE)

class Register:
    def __init__(self):
        # unnamed register and numbered registers 1–9
        self.named = {
            '"': None,
            **{str(i): None for i in range(1, 10)}
        }

    def set(self, entry, use_numbered=True):
        """
        Store an entry in the registers.
        entry: typically a tuple (item, subcalendar)
        use_numbered: if True, rotate numbered registers (1–9)
        """
        # unnamed register always gets the entry
        self.named['"'] = entry

        if use_numbered:
            # Shift registers 1–8 up
            for i in range(9, 1, -1):
                self.named[str(i)] = self.named.get(str(i - 1))
            self.named['1'] = entry

    def get(self, key='"'):
        """Retrieve an entry by register key (default is unnamed)."""
        return self.named.get(key)

    def clear(self, key='"'):
        self.named[key] = None
