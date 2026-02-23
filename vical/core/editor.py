# License: MIT (see LICENSE)

"""
Core editor state.
"""

from datetime import date, timedelta
from enum import Enum, auto

from vical.core.register import Register
from vical.settings import Settings, View
from vical.storage.jsonstore import load_subcalendars_local_json


SPLASH_TEXT = "vical v0.1 - Type :help for help or :q to quit"


class Status():
    def __init__(self):
        self.need_redraw = True
        self.redraw_counter = 0
        self.msg = (SPLASH_TEXT, 0)

    def request_redraw(self):
        self.need_redraw = True

    def notify(self, msg, error=False):
        self.msg = msg


class History():
    def __init__(self):
        self.current_tx = None
        self.saved_tx = None
        self.undo_stack = []
        self.redo_stack = []


class Editor():
    def __init__(self):
        self.settings = Settings()
        self.status = Status()
        self.history = History()
        self.registers = Register()
        self.subcalendars = load_subcalendars_local_json()

        self.selected_date = date.today()
        self.last_selected_date = self.selected_date
        self.visual_anchor_date = None
        self.last_visual_anchor_date = None

        self.selected_item_index = 0
        self.visual_anchor_item_index = None

        self.selected_subcal_index = 0
        
    @property
    def selected_subcal(self):
        return self.subcalendars[self.selected_subcal_index]

    @property
    def selected_item(self):
        items = self.get_items_for_selected_date()
        if not items:
            return None
        return items[self.selected_item_index % len(items)][1]

    @property
    def dirty(self):
        if not self.history.undo_stack:
            return False
        return self.history.saved_tx is not self.history.undo_stack[-1]

    @property
    def visual_active(self):
        return (
            self.visual_anchor_date is not None or
            self.visual_anchor_item_index is not None
        )

    def mark_saved(self):
        if self.undo_stack:
            self.history.saved_tx = self.undo_stack[-1]
        else:
            self.history.saved_tx = None

    def get_visual_selection_range(self):
        # TODO: support item selection
        if not self.visual_anchor_date:
            start = end = self.selected_date
        else:
            start = min(self.selected_date, self.visual_anchor_date)
            end = max(self.selected_date, self.visual_anchor_date)

        return (start, end)

    def get_items_in_visual_selection(self):
        # TODO: This only supports date selection.
        # It should support item selection as well.
        # Date selection should take precedence over item selection.
        if self.visual_anchor_date is not None:
            start = min(self.selected_date, self.visual_anchor_date)
            end = max(self.selected_date, self.visual_anchor_date)

            dates = []
            current = start
            while current <= end:
                dates.append(current)
                current += timedelta(days=1)

            return self.get_items_for_dates(dates)
        
        return self.selected_item

    def get_items_in_motion(self, motion):
        if isinstance(motion, DateMotion):
            dates = motion.expand()
            return self.get_items_for_dates(dates)

        if isinstance(motion, ItemMotion):
            indices = motion.expand()
            items = self.get_items_for_selected_date()

            if not items:
                return []

            # Clamp indices safely
            max_idx = len(items) - 1
            resolved = []

            for i in indices:
                if 0 <= i <= max_idx:
                    resolved.append(items[i])

            return resolved

        return []

    def get_item_by_uid(self, uid):
        for sc in self.subcalendars:
            for item in sc.items:
                if item.uid == uid:
                    return item
        return None

    def get_subcal_by_uid(self, uid):
        for sc in self.subcalendars:
            if sc.uid == uid:
                return sc

    def get_items_for_dates(self, dates):
        items = []

        for d in dates:
            for cal in self.subcalendars:
                if cal.hidden:
                    continue
                for item in cal.items:
                    if item.occurs_on(d):
                        items.append((cal, item))

        return items

    def get_items_for_selected_date(self):
        return self.get_items_for_dates([self.selected_date])

    def set_selected_date(self, target_date):
        if self._target_crosses_view_boundary(target_date):
            self.status.request_redraw()

        self.selected_date = target_date
        self.selected_item_index = 0


    def _target_crosses_view_boundary(self, target_date):
        """
        Used to trigger full redraws
        """
        if self.settings.view == View.MONTH:
            return (
                target_date.month != self.selected_date.month
                or target_date.year != self.selected_date.year
            )

        elif self.settings.view == View.WEEK:
            def week_start(d):
                # weekday(): Monday=0 … Sunday=6
                offset = (d.weekday() - self.settings.week_start) % 7
                return d - timedelta(days=offset)

            old_start = week_start(self.selected_date)
            new_start = week_start(target_date)
            return old_start != new_start