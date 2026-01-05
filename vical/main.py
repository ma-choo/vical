# vical/main.py
from .ui.ui_main import UI
from .subcalendar import Subcalendar, load_subcalendars

def main(stdscr):
    subcalendars = load_subcalendars()
    ui = UI(stdscr, subcalendars)
    ui.main_loop()
