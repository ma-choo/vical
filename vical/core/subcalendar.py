# License: MIT (see LICENSE)

"""
This module defines the core calendar item classes for vical.

CalendarItem: Base class.
Task: A to-do item with a single date and optional deadline.
Event: Item with a multiday date range.
Subcalendar: A named collection of CalendarItems.
"""

from datetime import date
import uuid


class CalendarItem:
    """
    Base class for calendar items
    """
    TYPE = "base"

    def __init__(
        self,
        uid: str | None,
        name: str,
        desc: str = "",
        remind: int = 0,
        parent_subcal: "Subcalendar" | None = None,
    ):
        self.uid = uid or uuid.uuid4().hex
        self.name = name
        self.desc = desc
        self.remind = remind
        # items know their parent subcal
        # this assists in undo/redo, paste/yank, and drawing logic.
        self.parent_subcal = parent_subcal

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError

    def sort_key(self):
        """
        Each item provides a sort key to order them consistently for display
        """
        raise NotImplementedError


class Task(CalendarItem):
    TYPE = "task"

    def __init__(
        self,
        uid: str | None,
        name: str,
        tdate: date | None = None,
        deadline: date | None = None,
        completed: bool = False,
        desc: str = "",
        remind: int = 0,
        parent_subcal: "Subcalendar" | None = None,
    ):
        super().__init__(uid, name, desc, remind, parent_subcal)
        self.date = tdate
        self.deadline = deadline
        self.completed = completed

    def occurs_on(self, day: date) -> bool:
        return self.date == day or self.deadline == day

    def sort_key(self):
        return (self.date or date.max, 1, self.name.lower())


class Event(CalendarItem):
    TYPE = "event"

    def __init__(
        self,
        uid: str | None,
        name: str,
        start_date: date | None = None,
        end_date: date | None = None,
        desc: str = "",
        remind: int = 0,
        parent_subcal: "Subcalendar" | None = None,
    ):
        super().__init__(uid, name, desc, remind, parent_subcal)
        self.start_date = start_date
        self.end_date = end_date
        if start_date and end_date and end_date < start_date:
            raise ValueError("Event end_date cannot be before start_date")

    def occurs_on(self, day: date) -> bool:
        if self.start_date and self.end_date:
            return self.start_date <= day <= self.end_date
        return False

    @property
    def duration(self) -> int:
        """
        Return the number of days the event spans.
        Used by smart paste to preserve event length.
        """
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def sort_key(self):
        return (self.start_date or date.max, 0, self.name.lower())


class Subcalendar:
    def __init__(self, uid: str | None, name: str, color: str = "green"):
        self.uid = uid or uuid.uuid4().hex
        self.name = name
        self.color = color
        self.hidden = False
        self.items: list[CalendarItem] = []


    # for loading subcalendars from disk
    # editor commands use transactions
    def insert_item(self, item: CalendarItem):
        item.parent_subcal = self
        self.items.append(item)
        self.items.sort(key=lambda i: i.sort_key())

    def toggle_hidden(self):
        self.hidden = not self.hidden
