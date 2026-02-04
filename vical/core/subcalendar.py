# subcalendar.py - Subcalendar class and calendar items (tasks, events).
# This file is part of vical.
# License: MIT (see LICENSE)

import uuid
from datetime import datetime, date, timedelta

from vical.core.register import RegisterPayload


class CalendarItem:
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
        self.parent_subcal = parent_subcal

    def remove(self):
        if not self.parent_subcal:
            raise RuntimeError("Item has no parent subcalendar")
        return self.parent_subcal.remove_item(self)

    def insert_into(self, target_subcal):
        self.parent_subcal = target_subcal
        target_subcal.insert_item(self)

    def occurs_on(self, day: date) -> bool:
        raise NotImplementedError

    @property
    def sort_date(self) -> date:
        raise NotImplementedError

    def sort_key(self):
        raise NotImplementedError

    def to_register(self) -> RegisterPayload:
        raise NotImplementedError

    @classmethod
    def from_register(cls, payload: RegisterPayload):
        if payload.kind == "task":
            return Task.from_register(payload)
        elif payload.kind == "event":
            return Event.from_register(payload)
        else:
            raise ValueError(f"Unknown payload kind: {payload.kind}")

    def to_dict(self) -> dict:
        raise NotImplementedError

    def base_dict(self) -> dict:
        d = {"type": self.TYPE, "uid": self.uid, "name": self.name}
        if self.desc:
            d["desc"] = self.desc
        if self.remind:
            d["remind"] = self.remind
        return d


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

    @property
    def sort_date(self) -> date:
        return self.date

    def sort_key(self):
        return (self.sort_date, 1, self.name.lower())

    def toggle_completed(self):
        self.completed = not self.completed

    def to_register(self):
        return RegisterPayload(
            kind="task",
            data={
                "name": self.name,
                "completed": self.completed,
                "deadline": self.deadline,
                "original_subcal_uid": self.parent_subcal.uid
            },
        )

    @classmethod
    def from_register(cls, payload):
        return cls(
            uid=None,
            name=payload.data["name"],
            tdate=None, # date is resolved on paste
            completed=payload.data.get("completed", False),
            deadline=payload.data.get("deadline"),
            parent_subcal=None,
        )

    def to_dict(self) -> dict:
        d = self.base_dict()
        if self.date:
            d["date"] = self.date.strftime("%Y%m%d")
        d["completed"] = self.completed
        if self.deadline:
            d["deadline"] = self.deadline.strftime("%Y%m%d")
        return d


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
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def sort_date(self) -> date:
        return self.start_date

    def sort_key(self):
        return (self.sort_date, 0, self.name.lower())

    def to_register(self):
        return RegisterPayload(
            kind="event",
            data={
                "name": self.name,
                # event start and end dates are set at paste,
                # but we preserve them in the payload so we can use
                # the duration property for smart paste.
                "start_date":self.start_date,
                "end_date":self.end_date,
                "original_subcal_uid": self.parent_subcal.uid
            },
        )

    @classmethod
    def from_register(cls, payload):
        return cls(
            uid=None,
            name=payload.data["name"],
            start_date=payload.data["start_date"],
            end_date=payload.data["end_date"],
            parent_subcal=None,
        )

    def to_dict(self) -> dict:
        d = self.base_dict()
        if self.start_date:
            d["start_date"] = self.start_date.strftime("%Y%m%d")
        if self.end_date:
            d["end_date"] = self.end_date.strftime("%Y%m%d")
        return d


class Subcalendar:
    def __init__(self, name: str, color: str = "green"):
        self.uid = uuid.uuid4().hex
        self.name = name
        self.color = color
        self.hidden = False
        self.items: list[CalendarItem] = []

    def insert_item(self, item: CalendarItem):
        item.parent_subcal = self
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
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subcalendar":
        sc = cls(
            name=data["name"],
            color=data.get("color", "green"),
        )
        for item_data in data.get("items", []):
            item = calendar_item_from_dict(item_data)
            sc.insert_item(item)
        return sc


def calendar_item_from_dict(data: dict) -> CalendarItem:
    item_type = data.get("type")
    if item_type == Task.TYPE:
        deadline = None
        if "deadline" in data:
            deadline = datetime.strptime(data["deadline"], "%Y%m%d").date()
        return Task(
            uid=data["uid"],
            name=data["name"],
            tdate=datetime.strptime(data["date"], "%Y%m%d").date(),
            deadline=deadline,
            completed=data.get("completed", False),
            desc=data.get("desc", ""),
        )
    if item_type == Event.TYPE:
        return Event(
            uid=data["uid"],
            name=data["name"],
            start_date=datetime.strptime(data["start_date"], "%Y%m%d").date(),
            end_date=datetime.strptime(data["end_date"], "%Y%m%d").date(),
            desc=data.get("desc", ""),
        )
    raise ValueError(f"Unknown calendar item type: {item_type}")