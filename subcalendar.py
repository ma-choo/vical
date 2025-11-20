import os
import json
from datetime import datetime

# persistent storage constants
DATA_DIR = os.path.expanduser("~/.local/share/calicula")
DATA_FILE = os.path.join(DATA_DIR, "subcalendars.json")

def save_subcalendars(subcalendars, filepath=DATA_FILE):
    """Save a list of Subcalendar objects to JSON (list-of-dicts)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = [sc.to_dict() for sc in subcalendars]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_subcalendars(filepath=DATA_FILE):
    """Load a list of Subcalendar objects from JSON. Returns a list."""
    if not os.path.exists(filepath):
        os.makedirs(DATA_DIR, exist_ok=True)
        default = Subcalendar("default", 1)
        save_subcalendars([default], filepath)
        return [default]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support old dict-by-name formats as a fallback
        if isinstance(data, dict):
            return [Subcalendar.from_dict(v) for v in data.values()]
        return [Subcalendar.from_dict(d) for d in data]
    except Exception as e:
        print(f"Failed to load {filepath}: {e}")
        # fallback to a single default calendar
        return [Subcalendar("default", 1)]

class Task:
    def __init__(self, name, date_str, completed=0):
        self.name = name
        self.date_str = date_str  # e.g. "20230811"
        self.completed = bool(completed)
        self.remind = 0
        self.date = datetime.strptime(date_str, "%Y%m%d").date()
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day
    
    def toggle_completed(self):
        self.completed = not self.completed

    def copy(self):
        return Task(self.name, self.date_str, int(self.completed))

    
    def to_dict(self):
        return {
            "name": self.name,
            "date_str": self.date_str,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["date_str"],
            data.get("completed", False),
        )

class Subcalendar:
    def __init__(self, name, color=1, hidden=False):
        self.name = name
        self.color = color
        self.hidden = hidden
        self.tasks = []
    
    def insert_task(self, task):
        self.tasks.append(task)
        self.tasks.sort(key=lambda a: (a.year, a.month, a.day, a.name))

    def pop_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            return task
        return None
    
    def toggle_hidden(self):
        self.hidden = not self.hidden
    
    def rename(self, new_name):
        self.name = new_name
    
    def change_color(self, color):
        self.color = color

    def to_dict(self):
        return {
            "name": self.name,
            "color": self.color,
            "hidden": self.hidden,
            "tasks": [t.to_dict() for t in self.tasks]
        }

    @classmethod
    def from_dict(cls, data):
        subcal = cls(data["name"], data.get("color", 1), data.get("hidden", False))
        for a_data in data.get("tasks", []):
            subcal.tasks.append(Task.from_dict(a_data))
        subcal.tasks.sort(key=lambda a: (a.year, a.month, a.day, a.name))
        return subcal