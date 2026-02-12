# normal.py - Normal mode input
# This file is part of vical.
# License: MIT (see LICENSE)

from vical.editor.editor import Mode
from vical.input import keys
from vical.input.command import execute_command
from vical.editor import movement


OPERATOR_KEYS = {}
MOTIONS = {}
NORMAL_KEYS = {}


def register_operator_key(key, func):
    OPERATOR_KEYS[key] = func


def register_motion_key(key, delta):
    MOTIONS[key] = delta


def register_normal_key(key, func):
    NORMAL_KEYS[key] = func


def normal_input(editor, key):
    """Handle a single keypress in NORMAL mode."""
    # ESC always resets
    if key == keys.ESC:
        editor.mode = Mode.NORMAL
        editor.operator = ""
        editor.count = ""
        editor.visual_anchor_date = None
        editor.redraw = True
        return

    # command mode
    if key == ord(':'):
        editor.prompt = {
            "label": ":",
            "user_input": "",
            "on_submit": lambda cmd: execute_command(editor, cmd),
        }
        editor.mode = Mode.PROMPT
        editor.redraw = True
        return

    # counts
    if ord('0') <= key <= ord('9'):
        editor.count += chr(key)
        return

    # visual mode
    if key == ord('v'):
        editor.mode = Mode.VISUAL
        return

    # operators
    if key in OPERATOR_KEYS:
        editor.operator = chr(key)
        editor.mode = Mode.OPERATOR_PENDING
        return

    # motions
    if key in MOTIONS:
        movement.move(editor, MOTIONS[key])
        editor.count = ""
        return

    # normal keys
    action = NORMAL_KEYS.get(key)
    if action:
        action(editor)
        editor.count = ""