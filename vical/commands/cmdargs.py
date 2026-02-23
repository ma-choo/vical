# License: MIT

"""
Command arguments.
"""

from datetime import date
from enum import Enum, auto
from typing import Optional, Callable

from vical.commands.motions import Motion


class Mode(Enum):
    NORMAL = auto()
    VISUAL = auto()
    INSERT = auto()
    EX_CMD = auto()
    PROMPT = auto()


class CmdArgs:
    key: str = ""                                   # Primary command key pressed
    next_key: str = ""                              # Secondary key for multi-key prefixes
    op_pending_key: str = ""                        # Operator key waiting for a motion
    motion_pending_cmd: Optional[Callable] = None   # Motion-pending command waiting for a motion
    motion: Optional[Motion] = None               # Current motion

    count_buffer: str = ""                          # Numeric input accumulated as string before conversion
    motion_count: int = 1                           # Multiplier applied to motions
    op_count: int = 1                               # Multiplier applied to operators
    special_count: int = 1                          # Special count for things like task repetition

    regname: str = '"'                              # Target register for yanks and deletes
    mode: Mode = Mode.NORMAL                        # Input mode

    ex_params: list[str] = None
    input_text: str = ""                            # Input text for commands or prompts

    last_op: str = ""                               # Last operator key for ! op_repeat
    last_date_before_goto = date.today() # Last selected date before a goto command.

    def clear(self):
        self.key = ""
        self.next_key = ""
        self.op_pending_key = ""
        self.motion_pending_cmd = None
        self.motion = None
        self.count_buffer = ""
        self.motion_count = 1
        self.op_count = 1
        self.special_count = 1
        self.input_text = ""
        self.ex_cmd_str = ""
        self.ex_cmd_parameters = None

    def clear_keys(self):
        self.key = ""
        self.next_key = ""