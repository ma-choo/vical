# visual.py - Visual mode input
# This file is part of vical.
# License: MIT (see LICENSE)

from vical.editor.editor import Mode
from vical.input import keys
from vical.editor import movement
from vical.editor.commands import new_event, paste_item_original_subcal, paste_item_selected_subcal


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
    def escape():
        editor.mode = Mode.NORMAL
        editor.visual_anchor_date = None
        editor.count = ""
        editor.redraw = True
        return

    if key == keys.ESC:
        escape()

    if ord('0') <= key <= ord('9'):
        editor.count += chr(key)
        return

    if key == ord('E'):
        new_event(editor)
        escape()

    if key == ord('p'):
        paste_item_original_subcal(editor)
        escape()

    if key == ord('P'):
        paste_item_selected_subcal(editor)
        escape()

    if key in MOTIONS:
        movement.move(editor, MOTIONS[key])
        editor.count = ""
        editor.redraw = True
        return
