# This file is part of Vical.
# License: MIT (see LICENSE)

import configparser
import os

# Default semantic mappings (color names only)
DEFAULT_SEMANTIC = {
    "FG": "white",
    "BG": "black",
    "ERROR": "red",
    "TODAY": "white, blue",  # fg, bg
    "DIM": "blue",
}

class ThemeConfig:
    def __init__(self, path=None):
        """
        Load theme config from INI file if provided.
        Fallback to default semantic mappings if file not found.
        Colors not defined in config are resolved by ThemeManager STANDARD_COLORS.
        """
        self.semantic = dict(DEFAULT_SEMANTIC)
        self.colors = {}  # arbitrary named colors from config (strings only)

        if path and os.path.exists(path):
            self._load_file(path)

    def _load_file(self, path):
        parser = configparser.ConfigParser()
        parser.read(path)

        # parse [colors] section
        if "colors" in parser:
            for key, value in parser["colors"].items():
                self.colors[key.lower()] = value  # value is just a string, e.g., "red" or "blue"

        # parse [semantic] section
        if "semantic" in parser:
            for key, value in parser["semantic"].items():
                self.semantic[key.upper()] = value

    def get_color(self, name):
        """Return configured color string, fallback to None (ThemeManager uses curses default)"""
        return self.colors.get(name.lower(), None)

    def get_semantic(self, name):
        """Return semantic mapping string for semantic name, fallback to default"""
        return self.semantic.get(name.upper(), DEFAULT_SEMANTIC.get(name.upper()))
