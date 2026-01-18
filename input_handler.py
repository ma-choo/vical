# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from vical.core import keys, movement, commands
from vical.core.input_helpers import handle_key, prompt_getch, prompt_getstr


KEYMAP = {}
MOTIONS = {}
OPERATORS = {}
COMMANDS = {}


def register_key(key, func): KEYMAP[key] = func
def register_motion(key, value): MOTIONS[key] = value
def register_operator(op, func): OPERATORS[op] = func
def register_command(name, func): COMMANDS[name] = func


def handle_key(ui):
    k = ui.stdscr.getch()
    if k == keys.RESIZE:
        ui.handle_resize()
    return k


def operator_goto(editor, key):
    k = chr(key)
    if k == 'g':
        movement.goto(editor)


def operator_delete(editor, key):
    k = chr(key)
    if k == 'd':
        commands.delete_task(editor)


def operator_change(editor, key):
    k = chr(key)
    if k == 'w':
        commands.rename_task(editor)


def init_default_keys():
    # motions
    register_motion(ord('h'),  -1)
    register_motion(keys.LEFT, -1)
    register_motion(ord('l'),   1)
    register_motion(keys.RIGHT, 1)
    register_motion(ord('k'),  -7)
    register_motion(keys.UP,   -7)
    register_motion(ord('j'),   7)
    register_motion(keys.DOWN,  7)
    # register_key(keys.CTRL_J,  movement.next_task)
    # register_key(keys.CTRL_K,  movement.prev_task)
    register_key(ord('['),     movement.prev_subcal)
    register_key(ord(']'),     movement.next_subcal)

    # normal mode keys
    register_key(ord('u'),   commands.undo)
    register_key(ord('U'),   commands.redo)
    register_key(ord('T'),   commands.new_task)
    register_key(keys.SPACE, commands.mark_complete)
    register_key(ord('C'),   commands.rename_task)
    register_key(ord('y'),   commands.yank_task)
    register_key(ord('D'),   commands.delete_task)
    register_key(ord('p'),   commands.paste_task)
    register_key(ord('P'),   commands.paste_task_to_selected_subcal)
    register_key(ord('z'),   commands.hide_subcal)

    # operators
    register_operator('g', operator_goto)
    register_operator('d', operator_delete)
    register_operator('c', operator_change)


def init_default_commands():
    register_command(":quit",       commands.quit)
    register_command(":q",          commands.quit)
    register_command(":quit!",      commands.quit_bang)
    register_command(":q!",         commands.quit_bang)
    register_command(":write",      commands.write)
    register_command(":w",          commands.write)
    register_command(":writequit",  commands.write_quit)
    register_command(":wq",         commands.write_quit)
    register_command(":undo",       commands.undo)
    register_command(":redo",       commands.redo)
    register_command(":help",       commands.show_help)
    register_command(":newtask",    commands.new_task)
    register_command(":complete",   commands.mark_complete)
    register_command(":renametask", commands.rename_task)
    register_command(":yank",       commands.yank_task)
    register_command(":paste",      commands.paste_task)
    register_command(":paste2",     commands.paste_task_to_selected_subcal)
    register_command(":deltask",    commands.delete_task)
    # register_command(":newcal",     commands.new_subcal)
    register_command(":renamecal",  commands.rename_subcal)
    register_command(":delcal",     commands.delete_subcal)
    register_command(":hide",       commands.hide_subcal)
    # register_command(":color",      commands.change_subcal_color)


def init_custom_keys():
    pass # TODO


def init_custom_commands():
    pass # TODO


def normal_mode_input(ui, editor, key):
    key_chr = chr(key) if 0 <= key <= 255 else ''

    # count buffer
    if '0' <= key_chr <= '9':
        editor.count_buffer += key_chr
        return

    # operator sequences
    if editor.operator:
        _apply_operator(editor, key)
        return

    if key_chr in OPERATORS:
        editor.operator = key_chr
        return

    # command mode
    if key == ord(':'):
        command = prompt_getstr(ui, "", ":")
        if command is None:
            editor.count_buffer = ''
            return
        _execute_command(editor, command)
        editor.count_buffer = ''
        return

    if key == keys.ESC:
        editor.operator = ''
        editor.count_buffer = ''
        return

    # motions
    if key in MOTIONS:
        movement.move(editor, MOTIONS[key])
        return

    # normal actions
    command = KEYMAP.get(key)
    if command:
        command(editor)


def _apply_operator(editor, key):
    handler = OPERATORS.get(editor.operator)
    if handler:
        handler(editor, key)   # pass the second key
    editor.operator = ''


def _execute_command(editor, commandstr):
    if not commandstr:
        return
    commandstr = commandstr.strip()
    command = COMMANDS.get(commandstr)
    if command:
        command(editor)
    else:
        editor.msg = (f"Unknown command: {commandstr}", 1)

