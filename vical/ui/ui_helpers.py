# vical/ui/ui_helpers
import curses
from . import keys
from .ui_draw import update_prompt


def handle_key(ui):
    k = ui.stdscr.getch()
    if k == keys.RESIZE:
        ui.handle_resize()
    return k


def prompt_getch(ui):
    while True:
        k = handle_key(ui)
        if k != keys.RESIZE:
            return k


def prompt_getstr(ui, text="", strarg=""):
    curses.curs_set(1)
    string = strarg

    while True:
        update_prompt(ui, f"{text}{string}")
        k = prompt_getch(ui)
        if k == keys.ESC:
            curses.curs_set(0)
            return None
        elif k in keys.ENTER: 
            return string
            break
        elif k in keys.BACKSPACE:
            if len(string) > 0:
                string = string[:-1]
        elif 32 <= k <= 126:
            string += chr(k)

    curses.curs_set(0)


def prompt_confirm(ui, text):
    update_prompt(ui, f"{text} (y/N)")
    key = ui.promptwin.getch()
    return chr(key).lower() == 'y'