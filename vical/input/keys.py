# This file is part of vical.
# License: MIT (see LICENSE)

import curses


SPACE = ord(' ')
ESC = 27
CTRL_J = 10
CTRL_K = 11
ENTER = {10, 13}
BACKSPACE = {curses.KEY_BACKSPACE, 127, 8}
LEFT = curses.KEY_LEFT
RIGHT = curses.KEY_RIGHT
UP = curses.KEY_UP
DOWN = curses.KEY_DOWN
RESIZE = curses.KEY_RESIZE


def handle_key(ui):
        k = ui.stdscr.getch()
        if k == RESIZE:
            ui.handle_resize()
        return k