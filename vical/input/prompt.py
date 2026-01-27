# prompt.py - Prompt mode input handling
# This file is part of vical.
# License: MIT (see LICENSE)

import curses

from vical.input import keys
from vical.core.editor import Mode
from vical.gui.draw import update_promptwin


def prompt_input(ui, editor, key):
        curses.curs_set(1)
        prompt = editor.prompt
        update_promptwin(ui, prompt["label"] + prompt["user_input"])

        if key == keys.ESC:
            curses.curs_set(0)
            editor.mode = Mode.NORMAL
            editor.prompt = None
            editor.redraw = True
            return

        if key in keys.ENTER:
            curses.curs_set(0)
            user_input = prompt["user_input"]
            editor.mode = Mode.NORMAL
            editor.prompt = None
            prompt["on_submit"](user_input)
            editor.redraw = True
            return

        if key in keys.BACKSPACE:
            prompt["user_input"] = prompt["user_input"][:-1]
        elif 32 <= key <= 126:
            prompt["user_input"] += chr(key)