# command.py - Command mode input
# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from vical.input.prompt import prompt_input, keys
from vical.core import commands
from vical.core.editor import Mode


# dict of command names to functions
COMMANDS = {}


def register_command(name, func):
    """Register a string to a command."""
    COMMANDS[name] = func


def command_input(ui, editor, key):
    if editor.prompt is None:
        editor.prompt = {
            "label": ":",
            "user_input": "",
            "on_submit": lambda cmd: _execute(editor, cmd),
        }
        editor.mode = Mode.PROMPT
        prompt_input(ui, editor, key)


def _execute(editor, cmd_str):
    command = COMMANDS.get(cmd_str)
    if command:
        command(editor)
    else:
        editor.msg = (f"Unkown command: {cmd_str}", 1)
        