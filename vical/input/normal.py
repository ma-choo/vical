# This file is part of vical.
# License: MIT (see LICENSE)

from vical.core.editor import Mode
from vical.input import keys
from vical.core import movement, commands


OPERATOR_KEYS = {
    ord('d'),
    ord('c'),
    ord('g'),
}


MOTIONS = {
    ord('h'): -1,
    keys.LEFT: -1,
    ord('l'): 1,
    keys.RIGHT: 1,
    ord('k'): -7,
    keys.UP: -7,
    ord('j'): 7,
    keys.DOWN: 7,
}


NORMAL_KEYS = {
    ord('u'): commands.undo,
    ord('U'): commands.redo,
    ord('T'): commands.new_task,
    keys.SPACE: commands.mark_complete,
    ord('y'): commands.yank_task,
    ord('p'): commands.paste_task,
    ord('z'): commands.hide_subcal,
    ord('['): movement.prev_subcal,
    ord(']'): movement.next_subcal,
}


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
