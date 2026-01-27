# state.py - Editor state capture and undo/redo support.
# This file is part of vical.
# License: MIT (see LICENSE)

from dataclasses import dataclass
from contextlib import contextmanager
import json
import hashlib
import copy

from vical.core.subcalendar import Task, Event


@dataclass
class State:
    subcalendars: list
    selected_subcal_index: int
    selected_item_index: int


def capture_state(editor) -> State:
    return State(
        subcalendars=copy.deepcopy(editor.subcalendars),
        selected_subcal_index=editor.selected_subcal_index,
        selected_item_index=editor.selected_item_index,
    )


def apply_state(editor, state: State):
    editor.subcalendars = copy.deepcopy(state.subcalendars)
    editor.selected_subcal_index = state.selected_subcal_index
    editor.selected_item_index = state.selected_item_index
    editor.redraw = True


def compute_state_id(editor):
    data = []
    for subcal in editor.subcalendars:
        tasks_data = []
        for item in subcal.items:
            if isinstance(item, Task):
                tasks_data.append((item.name, item.date.isoformat(), item.completed))
            elif isinstance(item, Event):
                tasks_data.append((item.name, item.start_date.isoformat(), item.end_date.isoformat()))
        data.append({
            "name": subcal.name,
            "color": subcal.color,
            "hidden": subcal.hidden,
            "tasks": tasks_data
        })
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.md5(serialized.encode()).hexdigest()


@contextmanager
def undoable(editor):
    """
    Context manager to wrap an action as undoable.
    """
    before_state = capture_state(editor)
    try:
        yield
    finally:
        after_state = capture_state(editor)
        change_id = compute_state_id(editor)

        editor.undo_stack.append((before_state, change_id))
        if len(editor.undo_stack) > editor.MAX_HISTORY:
            editor.undo_stack.pop(0)
        editor.redo_stack.clear()
        editor.state_id = change_id
