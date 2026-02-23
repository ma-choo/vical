# License: MIT (see LICENSE)

"""
Theme config loader.
"""

import configparser
import os


THEME_PATH = os.path.expanduser("~/.config/vical/theme.ini")


class ConfigLoader:
    def __init__(self):
        self.colors = {}
        self.pairs = {}

        if os.path.exists(THEME_PATH):
            self._load_config(THEME_PATH)

    def _load_config(self, path):
        parser = configparser.ConfigParser()
        parser.read(path)

        if "colors" in parser:
            for key, val in parser["colors"].items():
                self.colors[key.lower()] = val.strip()

        if "pairs" in parser:
            for key, val in parser["pairs"].items():
                self.pairs[key.lower()] = val.strip()

    def get_color(self, name):
        return self.colors.get(name.lower())

    def get_pair(self, name):
        return self.pairs.get(name.lower())
