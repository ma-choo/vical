"""
prompt.py - Prompt mode input handling
This file is part of vical.
License: MIT (see LICENSE)
"""

import curses
from vical.input import keys
from vical.core.editor import Mode
from vical.gui.draw import update_promptwin


def prompt_input(ui, editor, key):
        curses.curs_set(1)
        prompt = editor.prompt
        update_promptwin(ui, prompt["text"] + prompt["value"])

        if key == keys.ESC:
            curses.curs_set(0)
            editor.mode = Mode.NORMAL
            editor.prompt = None
            editor.redraw = True
            return

        if key in keys.ENTER:
            curses.curs_set(0)
            text = prompt["value"]
            editor.mode = Mode.NORMAL
            editor.prompt = None
            prompt["on_submit"](text)
            editor.redraw = True
            return

        if key in keys.BACKSPACE:
            prompt["value"] = prompt["value"][:-1]
        elif 32 <= key <= 126:
            prompt["value"] += chr(key)