# manager.py - Color theme manager.
# This file is part of Vical.
# License: MIT (see LICENSE)
import curses
from vical.theme.config import ConfigLoader


STANDARD_COLORS = {
    "default": -1,
    "black":   curses.COLOR_BLACK,
    "red":     curses.COLOR_RED,
    "green":   curses.COLOR_GREEN,
    "yellow":  curses.COLOR_YELLOW,
    "blue":    curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan":    curses.COLOR_CYAN,
    "white":   curses.COLOR_WHITE,
}


DEFAULT_PAIRS = {
    "error": "red, black",
    "today": "white, blue",
    "dim":   "blue",
}


class ThemeManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = ConfigLoader()

        curses.start_color()
        curses.use_default_colors()

        self.colors = dict(STANDARD_COLORS)
        self._extended_colors = {}

        # name -> curses pair number
        self.pairs = {}

        self._next_pair = 1
        self._init_pairs()

    def _resolve_color(self, name):
        if not isinstance(name, str):
            return STANDARD_COLORS["default"]

        val = self.config.get_color(name) or name
        val = val.strip().lower()

        # hex color
        if val.startswith("#") and len(val) == 7 and curses.can_change_color():
            if val in self._extended_colors:
                return self._extended_colors[val]

            idx = len(STANDARD_COLORS) + len(self._extended_colors)
            r, g, b = self._hex_to_rgb(val)

            try:
                curses.init_color(idx, r, g, b)
            except curses.error:
                return STANDARD_COLORS["default"]

            self._extended_colors[val] = idx
            return idx

        return STANDARD_COLORS.get(val, STANDARD_COLORS["default"])

    @staticmethod
    def _hex_to_rgb(hex_str):
        """
        Convert hex to curses rgb
        """
        r = int(hex_str[1:3], 16) * 1000 // 255
        g = int(hex_str[3:5], 16) * 1000 // 255
        b = int(hex_str[5:7], 16) * 1000 // 255
        return r, g, b

    def _alloc_pair(self, fg, bg="default"):
        fg_idx = self._resolve_color(fg)
        bg_idx = self._resolve_color(bg)

        pair = self._next_pair
        self._next_pair += 1

        try:
            curses.init_pair(pair, fg_idx, bg_idx)
        except curses.error:
            curses.init_pair(
                pair,
                STANDARD_COLORS["default"],
                STANDARD_COLORS["default"],
            )

        return pair

    def _init_pairs(self):
        for name, default_def in DEFAULT_PAIRS.items():
            pair_def = self.config.get_pair(name) or default_def
            parts = [p.strip() for p in pair_def.split(",")]

            fg = parts[0]
            bg = parts[1] if len(parts) > 1 else "default"

            self.pairs[name.lower()] = self._alloc_pair(fg, bg)

    def pair(self, name):
        """
        Return a curses color pair.

        - Semantic name -> predefined pair
        - Color name / hex -> fg on default bg
        """
        if not isinstance(name, str):
            name = "default"

        key = name.lower()

        if key not in self.pairs:
            # dynamic: treat as fg-on-default
            self.pairs[key] = self._alloc_pair(key)

        return self.pairs[key]
