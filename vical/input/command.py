# command.py - Command mode input
# This file is part of vical.
# License: MIT (see LICENSE)

import curses


# dict of command names to functions
COMMANDS = {}


def register_command(name, func):
    """Register a string to a command."""
    COMMANDS[name] = func


def execute_command(editor, cmd_str):
    command = COMMANDS.get(cmd_str)
    if command:
        command(editor)
    else:
        editor.msg = (f"Unkown command: {cmd_str}", 1)
        