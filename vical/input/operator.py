# This file is part of vical.
# License: MIT (see LICENSE)

from vical.core.editor import Mode
from vical.input import keys
from vical.core import movement, commands


def operator_pending_input(editor, key):
    op = editor.operator
    editor.operator = ""
    editor.mode = Mode.NORMAL

    # ESC cancels operator
    if key == keys.ESC:
        editor.count = ""
        return

    # operator-specific logic
    if op == 'd':
        _operator_delete(editor, key)
    elif op == 'c':
        _operator_change(editor, key)
    elif op == 'g':
        _operator_goto(editor, key)


def _operator_delete(editor, key):
    # dd - delete current task
    if key == ord('d'):
        commands.delete_task(editor)
        return


def _operator_change(editor, key):
    # cw - rename selected task
    if key == ord('w'):
        commands.rename_task(editor)
        return


def _operator_goto(editor, key):
    # gg - goto
    if key == ord('g'):
        movement.goto(editor)
    if key == ord('h'):
        movement.visual_left(editor)
    if key == ord('l'):
        movement.visual_right(editor)
    if key == ord('k'):
        movement.visual_up(editor)
    if key == ord('j'):
        movement.visual_down(editor)
