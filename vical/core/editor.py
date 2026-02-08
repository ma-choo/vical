# editor.py - Editor state management for vical
# This file is part of vical.
# License: MIT (see LICENSE)

"""
The Editor class centralizes the state and behavior of the vical interface.
It manages:
  Current mode (NORMAL, INSERT, VISUAL, OPERATOR_PENDING, COMMAND, PROMPT)
  Current view (MONTHLY, WEEKLY)
  Selected date and visual selection ranges
  Subcalendars and calendar items
  Registers for yanked items
  Undo/redo history

Selection:
  visual_anchor_date marks the start of a selection.
  selected_date always represents the active end of the selection.
  In NORMAL mode, no anchor is set; selection is a single date.
  The editor redraw logic relies on the anchor to render full selection ranges.

Calendar items:
  selected_item refers to the currently highlighted task or event on the selected date.
  Helper functions retrieve all visible items for a given date.
  Indices and scrolling are clamped to ensure valid selections.

Registers:
  registers store yanked CalendarItems as immutable payloads.
  Supports unnamed ('"') and numbered (1-9) registers with Vim-like rotation.

Undo/redo:
    - Transactions group multiple operations into a single atomic change.
    - `_current_tx` tracks the active transaction.
    - `undo_stack` and `redo_stack` implement a bounded history with `MAX_HISTORY`.
    - Changes to CalendarItems are recorded as operations and replayed or reverted.

- Redraw:
  `redraw` controls full and partial screen updates.
  This happens when a movement crosses a screen boundary or another action that warrants
  a full redraw, like adding or removing calendar items.
"""

from datetime import date, timedelta
from enum import Enum, auto

from vical.store.settings import Settings
from vical.storage.jsonstore import load_subcalendars
from vical.core.register import Register


class Mode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    OPERATOR_PENDING = auto()
    COMMAND = auto()
    PROMPT = auto()


SPLASH_TEXT = "vical v0.1 - Type :help for help or :q to quit"


class Editor:
    def __init__(self):
        self.mode = Mode.NORMAL
        self.prompt = None
        self.operator = ""
        self.count = ""
        self.last_motion = '0'
        self.msg = (SPLASH_TEXT, 0)

        self.selected_date = date.today()
        self.last_selected_date = self.selected_date
        self.visual_anchor_date: date | None = None  # start of visual selection
        self.last_visual_anchor_date = None
        self.first_visible_date = None

        self.subcalendars = load_subcalendars()
        self.subcalendar_map = {sc.uid: sc for sc in self.subcalendars}
        self.selected_subcal_index = 0
        self.selected_item_index = 0

        self.active_state = None
        self.saved_state = None
        self._current_tx = None
        self._saved_tx = None
        self.undo_stack = []
        self.redo_stack = []
        self.MAX_HISTORY = 50

        self.redraw = True
        self.redraw_counter = 0

        self.registers = Register()
        self.selected_register = '"'

        self.settings = Settings()

    def set_msg(self, msg, error=0): # TODO: this function name is not honest
        self.msg = (msg, error)

    def mark_for_redraw(self):
        self.redraw = True

    def mark_saved(self):
        """Mark current state as saved. Used for dirty checking."""
        if self.undo_stack:
            self._saved_tx = self.undo_stack[-1]
        else:
            self._saved_tx = None

    @property
    def dirty(self):
        """Return True if the editor has unsaved changes."""
        if not self.undo_stack:
            return False
        return self._saved_tx is not self.undo_stack[-1]

    def get_item_by_uid(self, uid: str) -> CalendarItem | None:
        for sc in self.subcalendars:
            for item in sc.items:
                if item.uid == uid:
                    return item
        return None

    def get_subcal_by_uid(self, uid: str) -> Subcalendar | None:
        return self.subcalendar_map.get(uid)

    @property
    def selected_subcal(self):
        return self.subcalendars[self.selected_subcal_index]

    @property
    def selected_item(self):
        """
        Return the currently selected calendar item.
        """
        items = self.get_items_for_selected_day()
        if not items:
            return None
        return items[self.selected_item_index % len(items)][1]

    def max_item_index(self):
        return max(0, len(self.get_items_for_selected_day()) - 1)

    def clamp_item_index(self):
        """
        Clamp the selected item index to a valid range for the selected day.
        """
        items = self.get_items_for_selected_day()
        if items:
            max_idx = len(items) - 1
            self.selected_item_index = min(self.selected_item_index, max_idx)
        else:
            self.selected_item_index = 0
            self.item_scroll_offset = 0

    def get_items_for_selected_day(self):
        """
        Collect all visible calendar items for the currently selected date.
        Returns a list of tuples: (subcalendar, item)
        """
        items = []
        for cal in self.subcalendars:
            if cal.hidden:
                continue
            for item in cal.items:
                if item.occurs_on(self.selected_date):
                    items.append((cal, item))
        return items

    def set_selected_date(self, new_date, *, reset_items: bool = True, record_motion: int | None = None):
        """
        Update the editor's selected date (normal mode) or selection range (visual mode).
        - VISUAL mode: visual_anchor_date is the start of the selection.
        - NORMAL mode: visual_anchor_date is cleared.
        """
        if self.view_boundary_crossed(new_date): # check if new date crosses view boundrary
            self.redraw = True # trigger full redraw
        # handle visual anchor
        # in visual mode selected_date is always the active end of the selection
        if self.mode == Mode.VISUAL:
            if self.visual_anchor_date is None:
                self.visual_anchor_date = self.selected_date
        else:
            self.visual_anchor_date = None

        self.last_selected_date = self.selected_date
        self.selected_date = new_date

        if reset_items:
            self.selected_item_index = 0
        else:
            self.clamp_item_index()

        if record_motion is not None:
            self.last_motion = f"{'+' if record_motion > 0 else ''}{record_motion}"
            self.count = ""

    def view_boundary_crossed(self, new_date):
        """
        Check whether a motion crosses a week, month, or year boundary.
        Used to trigger full redraws when calendar layout changes.
        """
        if self.view == View.MONTHLY:
            return (
                new_date.month != self.selected_date.month
                or new_date.year != self.selected_date.year
            )

        elif self.view == View.WEEKLY:
            def week_start(d):
                # weekday(): Monday=0 … Sunday=6
                offset = (d.weekday() - self.week_start) % 7
                return d - timedelta(days=offset)

            old_start = week_start(self.selected_date)
            new_start = week_start(new_date)
            return old_start != new_start

    # ---- history ----
    """
    def begin_transaction(self, label=""):
        if hasattr(self, "_current_tx") and self._current_tx is not None:
            raise RuntimeError("Nested transactions are not allowed")
        self._current_tx = Transaction(label)

    def record(self, op: Op):
        if not hasattr(self, "_current_tx") or self._current_tx is None:
            raise RuntimeError("record() called outside of transaction")
        self._current_tx.ops.append(op)

    def commit_transaction(self):
        if not hasattr(self, "_current_tx") or self._current_tx is None:
            return
        if not self._current_tx.ops:
            self._current_tx = None
            return
        self.undo_stack.append(self._current_tx)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.MAX_HISTORY:
            self.undo_stack.pop(0)
        self._current_tx = None

    def set_attr(self, item, attr, new):
        old = getattr(item, attr)
        if old == new:
            return

        self.record(OpSetAttr(item.uid, attr, old, new))
        setattr(item, attr, new)

    
    def undo(self):
        if not self.undo_stack:
            return
        tx = self.undo_stack.pop()
        tx.revert(self)
        self.redo_stack.append(tx)
        self.redraw = True

    def redo(self):
        if not self.redo_stack:
            return
        tx = self.redo_stack.pop()
        tx.apply(self)
        self.undo_stack.append(tx)
        self.redraw = True
    """