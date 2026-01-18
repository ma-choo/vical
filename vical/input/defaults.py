"""
defaults.py - default keybindings
This file is part of vical.
License: MIT (see LICENSE)
"""

from vical.core import commands
from vical.input.command import register


def register_default_commands():
    register("q", commands.quit)
    register("quit", commands.quit)

    register("q!", commands.quit_bang)
    register("quit!", commands.quit_bang)

    register("w", commands.write)
    register("write", commands.write)

    register("wq", commands.write_quit)
    register("writequit", commands.write_quit)

    register("undo", commands.undo)
    register("redo", commands.redo)
    register("help", commands.show_help)

    register("newtask", commands.new_task)
    register("complete", commands.mark_complete)
    register("nametask", commands.rename_task)
    register("deltask", commands.delete_task)

    register("newcal", commands.new_subcal)
    register("namecal", commands.rename_subcal)
    register("delcal", commands.delete_task)
