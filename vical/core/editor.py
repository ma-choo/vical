# editor.py - Editor state.
# This file is part of vical.
# License: MIT (see LICENSE)

from datetime import date, timedelta
from enum import Enum, auto

from vical.storage.jsonstore import load_subcalendars
from vical.core.register import Register
from vical.core.state import capture_state


SPLASH_TEXT = "vical 0.01 - type :help for help or :q to quit"


class Mode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    OPERATOR_PENDING = auto()
    COMMAND = auto()
    PROMPT = auto()


class View(Enum):
    MONTHLY = auto()
    WEEKLY = auto()


class Editor:
    def __init__(self):
        self.mode = Mode.NORMAL
        self.prompt = None
        self.operator = ""
        self.count = ""
        self.last_motion = '0'
        self.msg = (SPLASH_TEXT, 0)

        self.view = View.MONTHLY

        self.selected_date = date.today()
        self.last_selected_date = self.selected_date
        self.first_visible_date = None
        self.visual_anchor_date: date | None = None  # start of visual selection

        self.subcalendars = load_subcalendars()
        self.subcalendar_map = {sc.uid: sc for sc in self.subcalendars}
        self.selected_subcal_index = 0
        self.selected_item_index = 0

        self.active_state = capture_state(self)
        self.saved_state = self.active_state
        self.undo_stack = []
        self.redo_stack = []
        self.MAX_HISTORY = 50

        self.dim_when_completed = True
        self.week_start = 6 # 6 = sunday

        self.redraw = True
        self.redraw_counter = 0
        self.debug = True

        self.registers = Register()
        self.selected_register = '"'

    def mark_saved(self):
        self.saved_state = self.active_state

    @property
    def modified(self):
        return self.active_state != self.saved_state

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
