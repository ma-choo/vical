# License: MIT (see LICENSE)

"""
Key parser.
"""

import curses
from typing import Callable, Optional

from vical.commands.cmdargs import CmdArgs, Mode
from vical.commands.normal import NormalCmds
from vical.commands.ex_cmds import ExCmds
from vical.commands.utils import UtilCmds
from vical.input.defaults import init_default_keymap, init_default_cmdmap

ESC = 27
ENTER = {10, 13}
BACKSPACE = {curses.KEY_BACKSPACE, 127, 8}

# Flags
NEXT_KEY = 1 # Wait for next key
NEXT_KEY_NO_OP = 2 # get second char when no operator pending
KEEP_REG = 3 # don't clear regname


class KeyParser:
    def __init__(self, ui):
        self.editor = ui.editor
        self.cmdargs = CmdArgs()
        self.utils = UtilCmds(self.editor)
        self.nv_cmds = NormalCmds(self.editor, self.utils)
        self.ex_cmds = ExCmds(self.editor, self.utils)
        self.nvmap = init_default_keymap(self.nv_cmds)
        self.exmap = init_default_cmdmap(self.ex_cmds)
        self.input_buffer = ""
        self.input_label = ""

    def get_pending_keys(self):
        """
        Return a string of accumulative key presses to be displayed in the prompt.
        """
        c = self.cmdargs
        if c.mode in (Mode.NORMAL, Mode.VISUAL):
            return f"{c.count_buffer}{c.op_pending_key}{c.key}"
        elif c.mode == Mode.EX_CMD:
            return self.input_buffer

    def feed(self, key):
        """
        Main feed loop.
        Dispatches to normal or command mode.
        """
        if self.cmdargs.mode == Mode.EX_CMD:
            self._feed_command_mode(key)
        else:
            self._feed_normal_mode(key)

    def _feed_normal_mode(self, key: int):
        # Accumulate counts
        if ord('0') <= key <= ord('9') and not self.cmdargs.motion:
            self.cmdargs.count_buffer += chr(key)
            return

        # First or second key
        if not self.cmdargs.key:
            self.cmdargs.key = chr(key)
        elif not self.cmdargs.next_key:
            self.cmdargs.next_key = chr(key)
        else:
            self.cmdargs.clear()

        # Dispatch normal key
        cmd, flags = self.nvmap.get(self.cmdargs.key)
        if cmd:
            # if it's a NEXT_KEY command, wait for next_key
            if flags & NEXT_KEY:
                if not self.cmdargs.next_key:
                    # just store the key and return
                    return
            # otherwise, call immediately
            cmd(self.cmdargs)
            # clear keys after dispatch
            self.cmdargs.clear_keys()

    def _feed_command_mode(self, key: int):
        if key == ESC:
            self._exit_command_mode()
            return False

        elif key in ENTER:
            cmd_str = self.input_buffer.strip()

            if not cmd_str:
                self._exit_command_mode()
                return False

            # Split command string into command and parameters
            parts = cmd_str.split(maxsplit=1)
            ex_cmd_str = parts[0]
            self.cmdargs.ex_params = parts[1].split() if len(parts) > 1 else []

            self._execute_ex_command(ex_cmd_str)
            self._exit_command_mode()
            return True

        elif key in BACKSPACE:
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
            else:
                self._exit_command_mode()
                return False

        else:
            self.input_buffer += chr(key)

    def _exit_command_mode(self):
        self.cmdargs.mode = Mode.NORMAL
        self.input_buffer = ""
        self.input_label = ""

    def _execute_ex_command(self, ex_cmd_str):
        """
        Execute an Ex command string
        """
        cmd = self.exmap.get(ex_cmd_str)
        if cmd:
            cmd(self.cmdargs)
        else:
            self.editor.status.notify(f"Unknown command: {ex_cmd_str}", error=True)
