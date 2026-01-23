"""
editor.py - Editor state
This file is part of vical.
License: MIT (see LICENSE)
"""

from datetime import date
from enum import Enum, auto
from vical.core.subcalendar import load_subcalendars
from vical.core.state import capture_state, compute_state_id


class Mode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    OPERATOR_PENDING = auto()
    COMMAND = auto()
    PROMPT = auto()


class Editor:
    def __init__(self):
        self.subcalendars = load_subcalendars()

        self.mode = Mode.NORMAL
        self.prompt = None
        self.operator = ""
        self.count = ""
        self.last_motion = '0'
        self.msg = ("vical 0.01 - type :help for help or :q to quit", 0)

        self.selected_date = date.today()
        self.last_selected_date = self.selected_date
        self.selected_subcal_index = 0
        self.selected_task_index = 0
        self.task_scroll_offset = 0
        self.max_tasks_visible = 0

        initial_state = capture_state(self)
        self.state_id = compute_state_id(self)
        self.saved_state_id = self.state_id
        self.undo_stack = []
        self.redo_stack = []
        self.MAX_HISTORY = 50

        self.redraw = True
        self.redraw_counter = 0
        self.debug = True

        self.registers = {
            '"': None,  # unnamed register
            **{str(i): None for i in range(10)},                     # 0-9
            **{chr(c): None for c in range(ord('a'), ord('z') + 1)}  # a-z
        }

    @property
    def modified(self) -> bool:
        return self.state_id != self.saved_state_id

    @property
    def selected_subcal(self):
        return self.subcalendars[self.selected_subcal_index]

    @property
    def selected_task(self):
        tasks = self.get_tasks_for_selected_day()
        if not tasks:
            return None
        return tasks[self.selected_task_index % len(tasks)][1]

    def mark_saved(self):
        self.saved_state_id = self.state_id

    def get_tasks_for_day(self, year, month, day):
        tasks = []
        for cal in self.subcalendars:
            if cal.hidden:
                continue
            for t in cal.tasks:
                if (t.year, t.month, t.day) == (year, month, day):
                    tasks.append((cal, t))
        return tasks

    def get_tasks_for_selected_day(self):
        tasks = []
        for cal in self.subcalendars:
            if cal.hidden:
                continue
            for t in cal.tasks:
                if (t.year, t.month, t.day) == (self.selected_date.year, self.selected_date.month, self.selected_date.day):
                    tasks.append((cal, t))
        return tasks

    def clamp_task_index(self):
        tasks = self.get_tasks_for_selected_day()
        if tasks:
            max_idx = len(tasks) - 1
            self.selected_task_index = min(self.selected_task_index, max_idx)
        else:
            self.selected_task_index = 0
            self.task_scroll_offset = 0

    def set_date(self, new_date, *, reset_tasks: bool):
        if self.month_has_changed(new_date):
            self.redraw = True

        self.last_selected_date = self.selected_date
        self.selected_date = new_date

        if reset_tasks:
            self.selected_task_index = 0
            self.task_scroll_offset = 0
        else:
            self.clamp_task_index()

    def change_date(self, new_date, motion=0):
        self.set_date(new_date, reset_tasks=True)
        self.last_motion = f"{'+' if motion > 0 else ''}{motion}"
        self.count = ""

    def tasks_for_date(self, d):
        return self.get_tasks_for_day(d.year, d.month, d.day)

    def max_task_index(self):
        return max(0, len(self.get_tasks_for_selected_day()) - 1)

    def ensure_visible(self):
        if self.selected_task_index < self.task_scroll_offset:
            self.task_scroll_offset = self.selected_task_index
        elif self.selected_task_index >= self.task_scroll_offset + self.max_tasks_visible:
            self.task_scroll_offset = (
                self.selected_task_index - self.max_tasks_visible + 1
            )

    def month_has_changed(self, new_date):
        return (new_date.month != self.selected_date.month) or (new_date.year != self.selected_date.year)
