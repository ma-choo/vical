# state.py - Editor state capture and undo/redo support.
# This file is part of vical.
# License: MIT (see LICENSE)

from dataclasses import dataclass, field
from contextlib import contextmanager
import json
import hashlib
import copy

from vical.core.subcalendar import Task, Event


@dataclass(eq=False)
class State:
    subcalendars: list
    selected_subcal_index: int
    selected_item_index: int
    _id: str = field(init=False, repr=False)

    def __post_init__(self):
        self._id = self._compute_id()

    def _compute_id(self) -> str:
        data = []
        for subcal in self.subcalendars:
            items_data = []
            for item in subcal.items:
                if isinstance(item, Task):
                    items_data.append((
                        "task",
                        item.uid,
                        item.name,
                        item.date.isoformat(),
                        item.deadline.isoformat() if item.deadline else None,
                        item.completed,
                    ))
                elif isinstance(item, Event):
                    items_data.append((
                        "event",
                        item.uid,
                        item.name,
                        item.start_date.isoformat(),
                        item.end_date.isoformat(),
                    ))
            data.append((
                subcal.name,
                subcal.color,
                subcal.hidden,
                items_data,
            ))

        serialized = json.dumps(data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    # only compare ids when comparing states
    def __eq__(self, _state):
        if not isinstance(_state, State):
            return NotImplemented
        return self._id == _state._id


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
    editor.active_state = state
    editor.redraw = True


@contextmanager
def undoable(editor):
    """
    Context manager to wrap an action as undoable.
    """
    before = capture_state(editor)
    try:
        yield
    finally:
        after = capture_state(editor)

        if before != after:
            editor.undo_stack.append(before)
            if len(editor.undo_stack) > editor.MAX_HISTORY:
                editor.undo_stack.pop(0)

            editor.redo_stack.clear()
            editor.active_state = after
