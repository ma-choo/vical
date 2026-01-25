# subcalendar.py - Subcalendar and task objects
# This file is part of vical.
# License: MIT (see LICENSE)

import os
import json
from datetime import datetime, date
from typing import List


DATA_DIR = os.path.expanduser("~/.local/share/vical")
DATA_FILE = os.path.join(DATA_DIR, "subcalendars.json")


class Task:
    def __init__(self, name: str, tdate: date, completed: bool = False, remind: bool = False):
        self.name = name
        self.completed = completed
        self.remind = remind
        self.date = tdate

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def month(self) -> int:
        return self.date.month

    @property
    def day(self) -> int:
        return self.date.day

    def toggle_completed(self):
        self.completed = not self.completed

    def copy(self):
        return Task(self.name, self.date, self.completed)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "completed": self.completed,
            "remind": self.remind,
            "date": self.date.strftime("%Y%m%d")
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            name=data["name"],
            completed=data.get("completed", False),
            remind=data.get("remind", False),
            tdate=datetime.strptime(data["date"], "%Y%m%d").date()
        )


class Subcalendar:
    def __init__(self, name: str, color: str = "green", hidden: bool = False):
        self.name = name
        self.color = color
        self.hidden = hidden
        self.tasks: List[Task] = []

    def insert_task(self, task: Task):
        self.tasks.append(task)
        self.sort_tasks()

    def pop_task(self, task: Task):
        if task in self.tasks:
            self.tasks.remove(task)
            return task
        return None

    def sort_tasks(self):
        self.tasks.sort(key=lambda t: (t.year, t.month, t.day, t.name))

    def toggle_hidden(self):
        self.hidden = not self.hidden

    def rename(self, new_name: str):
        self.name = new_name

    def change_color(self, color: str):
        self.color = color

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "color": self.color,
            "hidden": self.hidden,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subcalendar":
        subcal = cls(
            name=data["name"],
            color=data.get("color", "green"),
            hidden=data.get("hidden", False),
        )

        for task_data in data.get("tasks", []):
            subcal.tasks.append(Task.from_dict(task_data))

        subcal.sort_tasks()
        return subcal


def save_subcalendars(subcalendars: List[Subcalendar], filepath: str = DATA_FILE):
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            [sc.to_dict() for sc in subcalendars],
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_subcalendars(filepath: str = DATA_FILE) -> List[Subcalendar]:
    if not os.path.exists(filepath):
        default = Subcalendar("default", 1) # default subcalendar
        save_subcalendars([default], filepath)
        return [default]

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Invalid vical data format: expected a list")

    return [Subcalendar.from_dict(d) for d in data]
