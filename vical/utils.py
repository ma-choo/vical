# vical/utils.py
import calendar
from datetime import date, datetime
from dataclasses import dataclass
from contextlib import contextmanager
import json
import hashlib
import copy


def contains_bad_chars(name: str) -> bool:
    invalid_chars = {'\t', '\n', '\r', '\x1b', ',', '<', '>', ':', '"', '/', '\\', '|'}
    if any(ch in invalid_chars for ch in name):
        return True
    if any(ord(ch) < 32 for ch in name):  # check for ascii control chars
        return True
    return False
    

def get_day_name(index: int) -> str:
    return calendar.day_abbr[(index + 6) % 7] # shift so sunday = 0


def get_month_name(month: int) -> str:
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    else:
        raise ValueError(f"Invalid month number: {month}")


def get_first_day_offset(month, year):
    return calendar.monthrange(year, month)[0] + 1


@dataclass
class UndoState:
    subcalendars: list
    selected_subcal_index: int
    selected_task_index: int


def capture_undo_state(ui) -> UndoState:
    return UndoState(
        subcalendars=copy.deepcopy(ui.subcalendars),
        selected_subcal_index=ui.selected_subcal_index,
        selected_task_index=ui.selected_task_index,
    )


def apply_undo_state(ui, state: UndoState):
    ui.subcalendars = copy.deepcopy(state.subcalendars)
    ui.selected_subcal_index = state.selected_subcal_index
    ui.selected_task_index = state.selected_task_index
    ui.redraw = True


def compute_change_id(ui):
    # compute a deterministic change id based on the current state of subcalendars and tasks
    data = []
    for subcal in ui.subcalendars:
        tasks_data = [(task.name, task.date.isoformat(), task.completed) for task in subcal.tasks]
        data.append({
            "name": subcal.name,
            "color": subcal.color,
            "hidden": subcal.hidden,
            "tasks": tasks_data
        })
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.md5(serialized.encode()).hexdigest()


@contextmanager
def undoable(ui):
    # undoable context using minimal state tracking for faster change_id computation
    before_state = capture_undo_state(ui)  # can still be a deepcopy for undo safety
    try:
        yield
    finally:
        after_state = capture_undo_state(ui)
        change_id = compute_change_id(ui)

        ui.undo_stack.append((before_state, change_id))
        if len(ui.undo_stack) > ui.MAX_HISTORY:
            ui.undo_stack.pop(0)
        ui.redo_stack.clear()
        ui.change_id = change_id
