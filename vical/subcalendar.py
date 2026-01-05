# vical/subcalendar.py
import os
import json
from datetime import datetime, date
from typing import List

DATA_DIR = os.path.expanduser("~/.local/share/vical")
DATA_FILE = os.path.join(DATA_DIR, "subcalendars.json")
DATE_FMT = "%Y%m%d"


class Task:
    def __init__(self, name: str, date_str: str, completed: bool = False):
        self.name = name
        self.date_str = date_str
        self.completed = bool(completed)

        self.date: date = datetime.strptime(date_str, DATE_FMT).date()
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day

    def toggle_completed(self):
        self.completed = not self.completed

    def copy(self):
        return Task(self.name, self.date_str, self.completed)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "date_str": self.date_str,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            name=data["name"],
            date_str=data["date_str"],
            completed=data.get("completed", False),
        )


class Subcalendar:
    def __init__(self, name: str, color: int = 1, hidden: bool = False):
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

    def change_color(self, color: int):
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
            color=data.get("color", 1),
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
