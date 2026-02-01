# subcalendar.py - Subcalendar and task objects
# This file is part of vical.
# License: MIT (see LICENSE)

import uuid
from datetime import datetime, date, timedelta


class CalendarItem:
    TYPE = "base"

    def __init__(self, uid: str | None, name: str, remind: bool = False):
        self.uid = uid or uuid.uuid4().hex
        self.name = name
        # self.desc = desc
        # self.parent_subcal = parent_subcal
        self.remind = remind

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError

    @property
    def sort_date(self) -> date:
        raise NotImplementedError

    def sort_key(self):
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError

    def base_dict(self) -> dict:
        return {
            "type": self.TYPE,
            "uid": self.uid,
            "name": self.name,
            "remind": self.remind,
        }


class Task(CalendarItem):
    TYPE = "task"

    def __init__(self, uid: str | None, name: str, tdate: date,
                 completed: bool = False, remind: bool = False):
        super().__init__(uid, name, remind)
        self.date = tdate
        # self.time = time
        # self.deadline = deadline
        self.completed = completed

    def occurs_on(self, day: date) -> bool:
        return self.date == day

    @property
    def sort_date(self) -> date:
        return self.date

    def sort_key(self):
        return (self.sort_date, 1, self.name.lower())

    def toggle_completed(self):
        self.completed = not self.completed

    def to_dict(self) -> dict:
        d = self.base_dict()
        d.update({
            "date": self.date.strftime("%Y%m%d"),
            "completed": self.completed,
        })
        return d


class Event(CalendarItem):
    TYPE = "event"

    def __init__(self, uid: str | None, name: str,
                 start_date: date, end_date: date,
                 remind: bool = False):
        super().__init__(uid, name, remind)
        if end_date < start_date:
            raise ValueError("Event end_date cannot be before start_date")
        self.start_date = start_date
        self.end_date = end_date

    def occurs_on(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date

    @property
    def duration(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def sort_date(self) -> date:
        return self.start_date

    def sort_key(self):
        return (self.sort_date, 0, self.name.lower())

    def to_dict(self) -> dict:
        d = self.base_dict()
        d.update({
            "start_date": self.start_date.strftime("%Y%m%d"),
            "end_date": self.end_date.strftime("%Y%m%d"),
        })
        return d


class Subcalendar:
    def __init__(self, name: str, color: str = "green", hidden: bool = False):
        self.name = name
        self.color = color
        self.hidden = hidden
        self.items: list[CalendarItem] = []

    def insert_item(self, item: CalendarItem):
        self.items.append(item)
        self.items.sort(key=lambda i: i.sort_key())
    
    def remove_item(self, item: CalendarItem) -> CalendarItem:
        self.items.remove(item)
        self.items.sort(key=lambda i: i.sort_key())
        return item

    def toggle_hidden(self):
        self.hidden = not self.hidden

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "color": self.color,
            "hidden": self.hidden,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subcalendar":
        sc = cls(
            name=data["name"],
            color=data.get("color", "green"),
            hidden=data.get("hidden", False),
        )

        for item_data in data.get("items", []):
            sc.items.append(calendar_item_from_dict(item_data))

        sc.items.sort(key=lambda i: i.sort_key())
        return sc


def calendar_item_from_dict(data: dict) -> CalendarItem:
    item_type = data.get("type")

    if item_type == Task.TYPE:
        return Task(
            uid=data["uid"],
            name=data["name"],
            tdate=datetime.strptime(data["date"], "%Y%m%d").date(),
            completed=data.get("completed", False),
            remind=data.get("remind", False),
        )

    if item_type == Event.TYPE:
        return Event(
            uid=data["uid"],
            name=data["name"],
            start_date=datetime.strptime(data["start_date"], "%Y%m%d").date(),
            end_date=datetime.strptime(data["end_date"], "%Y%m%d").date(),
            remind=data.get("remind", False),
        )

    raise ValueError(f"Unknown calendar item type: {item_type}")
    