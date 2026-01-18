"""
colors.py - Curses colors
This file is part of vical.
License: MIT (see LICENSE)
"""

import curses


class Colors:
    ERROR = 1
    TODAY = 2
    DIM = 3


DRACULA = {
    "bg":        (40, 42, 54),     # #282a36
    "fg":        (248, 248, 242),  # #f8f8f2
    "comment":   (98, 114, 164),   # #6272a4
    "purple":    (189, 147, 249),  # #bd93f9
    "red":       (255, 85, 85),    # #ff5555
    "cyan":      (139, 233, 253),  # #8be9fd
    "yellow":    (241, 250, 140),  # #f1fa8c
    "green":     (80, 250, 123),   # #50fa7b
    "pink":      (255, 121, 198),  # #ff79c6
}