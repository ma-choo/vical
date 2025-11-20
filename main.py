# main.py

import curses
from ui.ui_main import UI
from subcalendar import Subcalendar, load_subcalendars

def main(stdscr):
    subcalendars = load_subcalendars()
    if not subcalendars:
        default = Subcalendar("default", 1)
        subcalendars.append(default)

    ui = UI(stdscr, subcalendars)
    ui.main_loop()

if __name__ == "__main__":
    curses.set_escdelay(1)
    curses.wrapper(main)
