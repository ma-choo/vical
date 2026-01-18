# This file is part of Vical.
# License: MIT (see LICENSE)
import curses
import os
from vical.theme.config import ThemeConfig


THEME_PATH = os.path.expanduser("~/.config/vical/theme.ini")  # or wherever your config lives


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
        """
        stdscr: curses standard screen
        config: ThemeConfig instance
        """
        self.stdscr = stdscr
        self.config = ThemeConfig(path=THEME_PATH)  # <-- create instance

        curses.start_color()
        curses.use_default_colors()

        # map color name -> curses color index
        self.colors = dict(STANDARD_COLORS)

        # override colors with config-defined colors if present
        for name, value in self.config.colors.items():
            if value.lower() in STANDARD_COLORS:
                self.colors[name.lower()] = STANDARD_COLORS[value.lower()]
            # else: ignore, could extend later for RGB mapping

        # semantic pairs: name -> pair number
        self.pairs = {}

        # subcalendar pairs: arbitrary color string -> pair number
        self.subcal_pairs = {}

        self._init_semantic_pairs()

    def _init_semantic_pairs(self):
        """
        Initialize semantic color pairs:
        FG, BG, ERROR, TODAY, DIM
        """
        pair_num = 1

        # semantic definitions from config
        semantic_defs = ["FG", "BG", "ERROR", "TODAY", "DIM"]
        for name in semantic_defs:
            val = self.config.get_semantic(name)
            if val is None:
                val = name  # fallback to name itself

            # split fg/bg if comma exists, else fg only
            parts = [x.strip() for x in val.split(",")]
            fg_name = parts[0].lower()
            fg = self.colors.get(fg_name, self.colors["white"])
            bg = self.colors["black"]  # default bg
            if len(parts) > 1:
                bg_name = parts[1].lower()
                bg = self.colors.get(bg_name, self.colors["black"])

            curses.init_pair(pair_num, fg, bg)
            self.pairs[name.upper()] = pair_num
            pair_num += 1

        self._next_pair_num = pair_num

    def pair(self, semantic_name):
        """
        Return curses color pair index for semantic role.
        Fallback to FG if not defined.
        """
        return self.pairs.get(semantic_name.upper(), self.pairs["FG"])

    def subcal_pair(self, color_name):
        """
        Return curses color pair index for subcalendar color.
        Dynamically allocate if not already mapped.
        Uses fg=color_name, bg=BG (black by default).
        """
        color_name = color_name.lower()
        if color_name in self.subcal_pairs:
            return self.subcal_pairs[color_name]

        # resolve color name via config first, fallback to STANDARD_COLORS
        fg_name = self.config.get_color(color_name) or color_name
        fg = self.colors.get(fg_name.lower(), self.colors["white"])
        bg = self.colors.get("black", -1)

        pair_num = self._next_pair_num
        curses.init_pair(pair_num, fg, bg)
        self.subcal_pairs[color_name] = pair_num
        self._next_pair_num += 1
        return pair_num
