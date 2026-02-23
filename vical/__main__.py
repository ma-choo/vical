# License: MIT (see LICENSE)

"""
A terminal calendar and task manager with Vim-style keybindings.

Provides a minimal curses interface for navigating subcalendars, managing tasks
and events, and performing Vim-like operations (yank, paste, visual selection,
operator motions, undo/redo).
"""

import curses

from vical.core.editor import Editor
from vical.gui.curses_ui import CursesUI


def main(stdscr):
    editor = Editor()
    ui = CursesUI(stdscr, editor)
    ui.main()


def run():
    curses.set_escdelay(1)
    curses.wrapper(main)


if __name__ == "__main__":
    run()
