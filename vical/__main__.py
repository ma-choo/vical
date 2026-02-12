# main.py - Main program entry point.
# This file is part of vical.
# License: MIT (see LICENSE)

"""A terminal calendar and task manager with Vim-style keybindings.

Provides a minimal curses interface for navigating subcalendars, managing tasks
and events, and performing Vim-like operations (yank, paste, visual selection,
operator motions, undo/redo).
"""

import curses

from vical.gui.ui import CursesUI
from vical.editor.editor import Editor
from vical.input.defaults import register_default_keys, register_default_commands


def main(stdscr):
    register_default_keys()
    register_default_commands()
    editor = Editor()
    ui = CursesUI(stdscr)
    ui.main(editor)


def run():
    curses.set_escdelay(1)
    curses.wrapper(main)


if __name__ == "__main__":
    run()
