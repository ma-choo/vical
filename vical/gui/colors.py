"""
colors.py - Curses colors
This file is part of vical.
License: MIT (see LICENSE)
"""


ERROR = "ERROR"
TODAY = "TODAY"
DIM = "DIM"

"""
def init_colors(self):
    curses.start_color()
    curses.use_default_colors()

    if not curses.has_colors():
        return

    if curses.can_change_color():
        def rgb(r, g, b):
            return int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255)

        BASE = 20
        BG, FG, COMMENT, PURPLE, RED, CYAN, YELLOW, GREEN, PINK = range(BASE, BASE + 9)

        curses.init_color(BG, *rgb(40, 42, 54))
        curses.init_color(FG, *rgb(248, 248, 242))
        curses.init_color(COMMENT, *rgb(98, 114, 164))
        curses.init_color(PURPLE, *rgb(189, 147, 249))
        curses.init_color(RED, *rgb(255, 85, 85))
        curses.init_color(CYAN, *rgb(139, 233, 253))
        curses.init_color(YELLOW, *rgb(241, 250, 140))
        curses.init_color(GREEN, *rgb(80, 250, 123))
        curses.init_color(PINK, *rgb(255, 121, 198))

        curses.init_pair(1, RED, BG) # error
        curses.init_pair(2, FG, COMMENT) # today
        curses.init_pair(3, COMMENT, BG) # dim
        curses.init_pair(4, RED, BG)
        curses.init_pair(5, CYAN, BG)
        curses.init_pair(6, YELLOW, BG)
        curses.init_pair(7, GREEN, BG)
        curses.init_pair(8, PINK, BG)

    else:
        # fallback
        curses.init_pair(1, curses.COLOR_RED, -1) # error
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE) # today
        curses.init_pair(3, curses.COLOR_BLUE, -1) # dim
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_CYAN, -1)
        curses.init_pair(7, curses.COLOR_YELLOW, -1)
        curses.init_pair(8, curses.COLOR_GREEN, -1)
"""