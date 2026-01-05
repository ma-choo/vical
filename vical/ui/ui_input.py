# vical/ui/ui_input.py
import curses
from . import ui_actions
from .ui_draw import update_prompt

SPACE = ord(' ')
ESC = 27
CTRL_J = 10
CTRL_K = 11
ENTER = {10, 13}
BACKSPACE = {curses.KEY_BACKSPACE, 127, 8}


KEYMAP = {}    # key code -> action
MOTIONS = {}   # key code -> motion value
OPERATORS = {} # operator char -> operator handler
COMMANDS = {}  # string -> function


def register_key(key, func):
    KEYMAP[key] = func


def register_motion(key, value):
    MOTIONS[key] = value


def register_operator(op_char, func):
    OPERATORS[op_char] = func


def register_command(name, func):
    COMMANDS[name] = func


def operator_goto(ui, key):
    if key == ord('g'):
        ui_actions.goto(ui)


def operator_delete(ui, key):
    if key == ord('d'):
        ui_actions.delete_task(ui)


def operator_change(ui, key):
    if key == ord('w'):
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
    register_key(SPACE, ui_actions.mark_complete)
    register_key(CTRL_J, ui_actions.scroll_down)
    register_key(CTRL_K, ui_actions.scroll_up)
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
    register_command(":q!",     ui_actions.force_quit)
    register_command(":quit!",  ui_actions.force_quit)
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


def handle_key(ui):
    key = ui.stdscr.getch()
    if key == curses.KEY_RESIZE:
        ui.handle_resize()
    
    return key


def prompt_getch(ui):
    while True:
        key = handle_key(ui)
        if key != curses.KEY_RESIZE:
            return key


def prompt_getstr(ui):
    curses.curs_set(1)
    string = ''

    while True:
        update_prompt(ui, string)
        k = prompt_getch(ui)
        if k == ESC: break
        elif k in ENTER: 
            return string
            break
        elif k in BACKSPACE:
            if len(string) > 1:
                string = string[:-1]
        elif 32 <= k <= 126:
            string += chr(k)

    curses.curs_set(0)


def normal_mode_input(ui, key):
    if ord('0') <= key <= ord('9'):
        ui.count_buffer += chr(key)
        return

    if chr(key) in OPERATORS:
        if ui.operator:
            _apply_operator(ui, key)
        else:
            ui.operator = chr(key)
        return

    if key == ord(':'):
        _command_mode_input(ui)
        return

    if key == ESC:
        ui.operator = ''
        ui.count_buffer = ''
        return

    if key in MOTIONS:
        ui_actions.move(ui, MOTIONS[key])
        return

    action = KEYMAP.get(key)
    if action:
        action(ui)



def _apply_operator(ui, key):
    handler = OPERATORS.get(ui.operator)
    if handler: handler(ui, key)
    ui.operator = ''


def _command_mode_input(ui):
    curses.curs_set(1)
    command = ":"

    while True:
        update_prompt(ui, command)
        k = prompt_getch(ui)
        if k == ESC: break
        elif k in ENTER: 
            _execute_command(ui, command)
            break
        elif k in BACKSPACE:
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
