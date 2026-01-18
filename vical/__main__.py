"""
main.py - Main entry point.
This file is part of vical.
License: MIT (see LICENSE)
"""

import curses
from vical.gui.ui import CursesUI
from vical.core.editor import Editor
from vical.input.defaults import register_default_commands


def main(stdscr):
    register_default_commands()
    editor = Editor()
    ui = CursesUI(stdscr)
    ui.main(editor)


def run():
    curses.set_escdelay(1)
    curses.wrapper(main)


if __name__ == "__main__":
    run()
