# vical/__main__.py
import curses
from .main import main

def run():
    curses.set_escdelay(1)
    curses.wrapper(main)

if __name__ == "__main__":
    run()
