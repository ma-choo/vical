# ViCal
ViCal is a terminal-based calendar and task manager with Vi-like motions and commands.

![Screenshot](images/screenshot.png)

## Features
- Vi-like motions and commands
- Full monthly calendar display
- Edit, delete, and mark tasks as completed
- Multiple subcalendars for organizing tasks
- Color-coded and hideable subcalendars

## Installation
Clone the repo:
```bash
git clone https://github.com/ma-choo/calicula.git
cd vical
```

Run without installing:
```bash
python -m vical
```

Install with pip:
```bash
pip install .
```

Run with:
```bash
vical
```

## Storage
Calicula stores your subcalendars and tasks as JSON in `~/.local/share/vical/subcalendars.json`