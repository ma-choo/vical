# This file is part of Vical.
# License: MIT (see LICENSE)

import curses
import os
from vical.theme.config import ThemeConfig


# Standard 8-terminal colors
STANDARD_COLORS = {
    "black": -1,  # default terminal background
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
}


class ThemeManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = ThemeConfig()

        curses.start_color()
        curses.use_default_colors()

        self.colors = dict(STANDARD_COLORS)  # name -> curses color index

        # Map config-defined colors to curses index if terminal supports it
        self._extended_colors = {}
        if curses.can_change_color():
            # terminal supports custom colors
            pass  # We'll allocate RGB slots on demand

        # semantic pairs: name -> pair number
        self.pairs = {}

        # subcalendar pairs: arbitrary color string -> pair number
        self.subcal_pairs = {}

        # start pair numbers at 1
        self._next_pair_num = 1

        self._init_semantic_pairs()

    @staticmethod
    def _hex_to_rgb(hex_str: str):
        """
        Convert #RRGGBB to 0-1000 curses RGB.
        """
        r = int(hex_str[1:3], 16) * 1000 // 255
        g = int(hex_str[3:5], 16) * 1000 // 255
        b = int(hex_str[5:7], 16) * 1000 // 255
        return r, g, b

    def _resolve_color(self, name: str):
        """
        Resolve a color name or hex string to a curses color index.
        Returns standard curses color index if terminal can't change colors.
        """
        val = self.config.get_color(name) or name  # hex or name
        val = val.strip().lower()

        if val.startswith("#") and len(val) == 7 and curses.can_change_color():
            # allocate a new curses color for this hex if not already
            if val in self._extended_colors:
                return self._extended_colors[val]

            # pick next available color index (start after standard 0-7)
            color_index = len(STANDARD_COLORS) + len(self._extended_colors)
            r, g, b = self._hex_to_rgb(val)
            try:
                curses.init_color(color_index, r, g, b)
            except curses.error:
                # fallback if terminal can't change color
                color_index = STANDARD_COLORS.get("white", 7)
            self._extended_colors[val] = color_index
            return color_index
        else:
            # fallback to standard color
            return STANDARD_COLORS.get(val, STANDARD_COLORS["white"])

    def _alloc_color_pair(self, name: str, fg_name: str, bg_name: str = "black"):
        """
        Allocate a curses color pair for semantic or subcalendar use.
        """
        fg = self._resolve_color(fg_name)
        bg = self._resolve_color(bg_name)

        pair_num = self._next_pair_num
        try:
            curses.init_pair(pair_num, fg, bg)
        except curses.error:
            # fallback to white on black
            curses.init_pair(pair_num, STANDARD_COLORS["white"], STANDARD_COLORS["black"])
        self._next_pair_num += 1
        return pair_num

    def _init_semantic_pairs(self):
        """
        Initialize semantic color pairs using config or defaults.
        """
        semantic_defs = ["FG", "BG", "ERROR", "TODAY", "DIM"]
        for name in semantic_defs:
            val = self.config.get_semantic(name)
            parts = [x.strip() for x in val.split(",")]
            fg_name = parts[0]
            bg_name = parts[1] if len(parts) > 1 else "black"
            pair_num = self._alloc_color_pair(name, fg_name, bg_name)
            self.pairs[name.upper()] = pair_num

    def pair(self, semantic_name: str):
        """Return curses color pair index for semantic role, fallback to FG."""
        return self.pairs.get(semantic_name.upper(), self.pairs["FG"])

    def subcal_pair(self, color_name: str):
        """Return curses color pair for a subcalendar color, allocate if needed."""
        if not isinstance(color_name, str):
            color_name = "white"  # or fallback
            
        color_name = color_name.lower()
        if color_name in self.subcal_pairs:
            return self.subcal_pairs[color_name]

        pair_num = self._alloc_color_pair(f"subcal_{color_name}", color_name)
        self.subcal_pairs[color_name] = pair_num
        return pair_num
