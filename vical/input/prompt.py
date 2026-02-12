# prompt.py - Prompt mode input handling
# This file is part of vical.
# License: MIT (see LICENSE)

# TODO: make prompt mode fully modal and reusable (search, rename, command)

import curses

from vical.input import keys, command
from vical.editor.editor import Mode
from vical.gui.draw import update_promptwin


def prompt_input(ui, editor, key):
    prompt = editor.prompt

    if key == keys.ESC:
        editor.mode = Mode.NORMAL
        editor.prompt = None
        editor.redraw = True
        return

    if key in keys.ENTER:
        user_input = prompt["user_input"]
        editor.mode = Mode.NORMAL
        editor.prompt = None
        prompt["on_submit"](user_input)
        editor.redraw = True
        return

    if key in keys.BACKSPACE:
        if not prompt["user_input"]:
            # exit prompt
            editor.mode = Mode.NORMAL
            editor.prompt = None
            editor.redraw = True
            return
        else:
            prompt["user_input"] = prompt["user_input"][:-1]

    elif 32 <= key <= 126:
        prompt["user_input"] += chr(key)
