# jsonstore.py
# This file is part of vical.
# License: MIT (see LICENSE)

"""
Json storage.
"""

from datetime import datetime
import json
import os
from typing import List

from vical.core.subcalendar import CalendarItem, Task, Event, Subcalendar

DATA_DIR = os.path.expanduser("~/.local/share/vical")
DATA_FILE = os.path.join(DATA_DIR, "subcalendars.json")


def calitem_to_dict(item) -> dict:
    # base item dict
    d = {"type": item.TYPE, "uid": item.uid, "name": item.name}
    if item.desc:
        d["desc"] = item.desc
    if item.remind:
        d["remind"] = item.remind
    if item.TYPE == "task":
        if item.date:
            d["date"] = item.date.strftime("%Y%m%d")
        d["completed"] = item.completed
        if item.deadline:
            d["deadline"] = item.deadline.strftime("%Y%m%d")
    if item.TYPE == "event":
        if item.start_date:
            d["start_date"] = item.start_date.strftime("%Y%m%d")
        if item.end_date:
            d["end_date"] = item.end_date.strftime("%Y%m%d")

    return d


def calitem_from_dict(data: dict) -> CalendarItem:
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


def subcal_to_dict(sc) -> dict:
    return {
        "uid": sc.uid,
        "name": sc.name,
        "color": sc.color,
        "items": [calitem_to_dict(item) for item in sc.items],
    }


def subcal_from_dict(data: dict) -> Subcalendar:
    sc = Subcalendar(
        uid=data["uid"],
        name=data["name"],
        color=data.get("color", "green"),
    )
    for item_data in data.get("items", []):
        item = calitem_from_dict(item_data)
        sc.insert_item(item)
    return sc


def save_subcalendars_local_json(
    subcalendars: List[Subcalendar],
    filepath: str = DATA_FILE,
) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            [subcal_to_dict(sc) for sc in subcalendars],
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_subcalendars_local_json(filepath: str = DATA_FILE) -> List[Subcalendar]:
    if not os.path.exists(filepath):
        default = Subcalendar(None, "Default")
        return [default]

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Invalid vical data format: expected a list")

    return [subcal_from_dict(d) for d in data]
