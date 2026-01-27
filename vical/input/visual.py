# visual.py - Visual mode input
# This file is part of vical.
# License: MIT (see LICENSE)

from vical.core.editor import Mode
from vical.input import keys
from vical.core import movement
from vical.core.commands import new_event


MOTIONS = {
    ord('h'): -1,   # left
    ord('l'): 1,    # right
    ord('k'): -7,   # up (one week back)
    ord('j'): 7,    # down (one week forward)
}


def visual_input(editor, key):
    """
    Handle a single keypress in VISUAL mode.
    Only movement keys adjust the selection.
    ESC exits visual mode.
    """
    # ESC exits visual mode
    if key == keys.ESC:
        editor.mode = Mode.NORMAL
        editor.visual_anchor_date = None
        editor.redraw = True
        return

    if ord('0') <= key <= ord('9'):
        editor.count += chr(key)
        return

    if key == ord('e'):
        new_event(editor)

    if key in MOTIONS:
        movement.move(editor, MOTIONS[key])
        editor.count = ""
        editor.redraw = True
        return
