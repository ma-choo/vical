# vical/ui/ui_input.py
import curses
from . import keys
from . import ui_actions
from .ui_helpers import keys, handle_key, prompt_getch
from .ui_draw import update_prompt


KEYMAP = {}
MOTIONS = {}
OPERATORS = {}
COMMANDS = {}


def register_key(key, func):
    KEYMAP[key] = func


def register_motion(key, value):
    MOTIONS[key] = value


def register_operator(op, func):
    OPERATORS[op] = func


def register_command(name, func):
    COMMANDS[name] = func


def operator_goto(ui, key):
    k = chr(key)
    if k == 'g':
        ui_actions.goto(ui)


def operator_delete(ui, key):
    k = chr(key)
    if k == 'd':
        ui_actions.delete_task(ui)


def operator_change(ui, key):
    k = chr(key)
    if k == 'w':
        ui_actions.rename_task(ui)


def init_default_keys():
    # normal mode keys
    register_key(ord('u'), ui_actions.undo)
    register_key(ord('U'), ui_actions.redo)
    register_key(ord('T'), ui_actions.new_task)
    register_key(ord('D'), ui_actions.delete_task)
    register_key(ord('y'), ui_actions.yank_task)
    register_key(ord('R'), ui_actions.rename_task)
    register_key(ord('p'), ui_actions.paste_task)
    register_key(ord('P'), ui_actions.paste_task_to_selected_subcal)
    register_key(ord('z'), ui_actions.hide_subcal)
    register_key(keys.SPACE,    ui_actions.mark_complete)
    register_key(keys.CTRL_J,   ui_actions.scroll_down)
    register_key(keys.CTRL_K,   ui_actions.scroll_up)
    register_key(ord('C'), ui_actions.rename_subcal)
    register_key(ord('['), ui_actions.prev_subcal)
    register_key(ord(']'), ui_actions.next_subcal)

    # motions
    register_motion(ord('h'), -1)
    register_motion(curses.KEY_LEFT, -1)
    register_motion(ord('l'), 1)
    register_motion(curses.KEY_RIGHT, 1)
    register_motion(ord('j'), 7)
    register_motion(curses.KEY_DOWN, 7)
    register_motion(ord('k'), -7)
    register_motion(curses.KEY_UP, -7)

    register_operator('g', operator_goto)
    register_operator('d', operator_delete)
    register_operator('c', operator_change)


def init_default_commands():
    register_command(":w",      ui_actions.write)
    register_command(":write",  ui_actions.write)
    register_command(":q",      ui_actions.quit)
    register_command(":quit",   ui_actions.quit)
    register_command(":wq",     ui_actions.write_quit)
    register_command(":q!",     ui_actions.quit_bang)
    register_command(":quit!",  ui_actions.quit_bang)
    register_command(":help",   ui_actions.show_help)
    register_command(":undo",   ui_actions.undo)
    register_command(":redo",   ui_actions.redo)
    register_command(":nc",     ui_actions.new_subcal)
    register_command(":dc",     ui_actions.delete_subcal)
    register_command(":color",  ui_actions.change_subcal_color)


def init_custom_keys():
    pass # TODO


def init_custom_commands():
    pass # TODO


def normal_mode_input(ui, key):
    key_chr = chr(key)

    if ord('0') <= key <= ord('9'):
        ui.count_buffer += key_chr
        return

    # operator sequences
    if ui.operator:
        # second key pressed, call the operator handler
        handler = OPERATORS.get(ui.operator)
        if handler:
            handler(ui, key)   # pass the second key as motion
        ui.operator = ''
        return

    # first key pressed, start operator if it exists
    if key_chr in OPERATORS:
        ui.operator = key_chr
        return

    # command mode
    if key == ord(':'):
        _command_mode_input(ui)
        return

    if key == keys.ESC:
        ui.operator = ''
        ui.count_buffer = ''
        return

    # motions
    if key in MOTIONS:
        ui_actions.move(ui, MOTIONS[key])
        return

    # normal actions
    action = KEYMAP.get(key)
    if action:
        action(ui)


def _apply_operator(ui, key):
    handler = OPERATORS.get(ui.operator)
    if handler:
        handler(ui, key)   # pass the second key
    ui.operator = ''


def _command_mode_input(ui):
    curses.curs_set(1)
    command = ":"

    while True:
        update_prompt(ui, command)
        k = prompt_getch(ui)
        if k == keys.ESC: break
        elif k in keys.ENTER: 
            _execute_command(ui, command)
            break
        elif k in keys.BACKSPACE:
            if len(command) > 1:
                command = command[:-1]
        elif 32 <= k <= 126:
            command += chr(k)
    curses.curs_set(0)

    ui.count_buffer = ''


def _execute_command(ui, command):
    command = command.strip()
    action = COMMANDS.get(command)
    if action:
        action(ui)
    else:
        ui.msg = (f"Unknown command: {command}", 1)
