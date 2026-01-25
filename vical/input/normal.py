# normal.py - Normal mode input
# This file is part of vical.
# License: MIT (see LICENSE)

from vical.core.editor import Mode
from vical.input import keys
from vical.core import movement, commands


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
        editor.operator = ""
        editor.count = ""
        return

    # ':' enters command mode
    if key == ord(':'):
        editor.mode = Mode.COMMAND
        return

    # counts
    if ord('0') <= key <= ord('9'):
        editor.count += chr(key)
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

    # simple commands
    action = NORMAL_KEYS.get(key)
    if action:
        action(editor)
        editor.count = ""
