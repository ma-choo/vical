"""
defaults.py - Default keybindings and commands.
This file is part of vical.
License: MIT (see LICENSE)
"""

from vical.core import commands
from vical.input import keys
from vical.input.normal import register_normal_key, register_operator_key, register_motion_key
from vical.input.command import register_command


def register_default_keys():
    register_normal_key(ord('u'),   commands.undo)
    register_normal_key(ord('U'),   commands.redo)
    register_normal_key(ord('T'),   commands.new_task)
    register_normal_key(ord('E'),   commands.new_event)
    register_normal_key(keys.SPACE, commands.mark_complete)
    register_normal_key(ord('y'),   commands.yank_item)
    register_normal_key(ord('p'),   commands.paste_item)
    register_normal_key(ord('z'),   commands.hide_subcal)
    register_normal_key(ord('['),   commands.prev_subcal)
    register_normal_key(ord(']'),   commands.next_subcal)

    # motions
    register_motion_key(ord('h'), -1)
    register_motion_key(keys.LEFT, -1)
    register_motion_key(ord('l'), 1)
    register_motion_key(keys.RIGHT, 1)
    register_motion_key(ord('k'), -7)
    register_motion_key(keys.UP, -7)
    register_motion_key(ord('j'), 7)
    register_motion_key(keys.DOWN, 7)

    # operators
    register_operator_key(ord('d'), None)
    register_operator_key(ord('c'), None)
    register_operator_key(ord('g'), None)


def register_default_commands():
    register_command("q",           commands.quit)
    register_command("quit",        commands.quit)

    register_command("q!",          commands.quit_bang)
    register_command("quit!",       commands.quit_bang)

    register_command("w",           commands.write)
    register_command("write",       commands.write)

    register_command("wq",          commands.write_quit)
    register_command("writequit",   commands.write_quit)

    register_command("undo",        commands.undo)
    register_command("redo",        commands.redo)
    register_command("help",        commands.show_help)

    register_command("newtask",     commands.new_task)
    register_command("newevent",    commands.new_event)
    register_command("complete",    commands.mark_complete)
    register_command("rename",      commands.rename_item)
    register_command("delete",      commands.delete_item)

    register_command("newcal",      commands.new_subcal)
    register_command("renamecal",   commands.rename_subcal)
    register_command("delcal",      commands.delete_subcal)
    register_command("hide",        commands.hide_subcal)
    register_command("color",       commands.change_subcal_color)
    register_command("month",       commands.toggle_monthly_view)
    register_command("week",        commands.toggle_weekly_view)
