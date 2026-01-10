# vical/ui/ui_main.py
import curses
import copy
import hashlib
import json
import time
from datetime import date
from .ui_draw import draw_screen
from .ui_helpers import handle_key
from .ui_input import init_default_keys, init_default_commands, normal_mode_input
from ..utils import capture_undo_state, compute_change_id


class UI:
    def __init__(self, stdscr, subcalendars):
        self.stdscr = stdscr
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # mainwin: 6 rows x 7 columns grid
        self.mainwin_hfactor = (self.screen_h - 2) // 6
        self.mainwin_wfactor = (self.screen_w - 2) // 7
        self.mainwin_h = self.mainwin_hfactor * 6 + 1
        self.mainwin_w = self.mainwin_wfactor * 7 + 1
        self.mainwin_y = 0
        self.mainwin_x = 0

        # prompt line
        self.promptwin_h = 1
        self.promptwin_w = self.screen_w
        self.promptwin_y = self.mainwin_h
        self.promptwin_x = 0

        self.init_color_pairs()
        self.init_windows()

        # state
        self.subcalendars = subcalendars
        self.selected_subcal_index = 0
        self.cell_scroll_index = 0
        self.selected_task_index = 0
        self.task_scroll_offset = 0

        self.last_motion = '0'
        self.count_buffer = ""
        self.operator = ""

        self.msg = ("calicula 0.01 - type :help for help or :q for quit", 0)
        self.HELP = "todo"

        self.selected_date = date.today()
        self.last_selected_date = self.selected_date

        # history
        self.MAX_HISTORY = 50
        self.undo_stack = []
        self.redo_stack = []
        initial_state = capture_undo_state(self)
        self.change_id = compute_change_id(initial_state)
        self.saved_change_id = self.change_id

        self.registers = {
            '"': None,  # unnamed register
            **{str(i): None for i in range(10)},                     # 0-9
            **{chr(c): None for c in range(ord('a'), ord('z') + 1)}  # a-z
        }

        self.running = True
        self.redraw = True
        self.redraw_counter = 0
        self.debug = False

        init_default_keys()
        init_default_commands()
        self.stdscr.refresh()


    @property
    def modified(self) -> bool:
        return self.change_id != self.saved_change_id


    def init_color_pairs(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_GREEN, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)  # current date highlight


    def init_windows(self):
        self.mainwin = curses.newwin(self.mainwin_h, self.mainwin_w, self.mainwin_y, self.mainwin_x)
        self.promptwin = curses.newwin(self.promptwin_h, self.promptwin_w, self.promptwin_y, self.promptwin_x)

    def handle_resize_old(self):
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # recalc layout
        self.mainwin_hfactor = max(1, (self.screen_h - 2) // 6)
        self.mainwin_wfactor = max(1, (self.screen_w - 2) // 7)
        self.mainwin_h = self.mainwin_hfactor * 6 + 1
        self.mainwin_w = self.mainwin_wfactor * 7 + 1

        self.promptwin_y = min(self.mainwin_h, self.screen_h - 1)
        self.promptwin_w = self.screen_w
        self.promptwin_h = 1
        self.promptwin_x = 0
        self.mainwin_y = 0
        self.mainwin_x = 0

        # rebuild windows
        del self.mainwin, self.promptwin
        self.init_windows()

        # mark for full redraw
        self.redraw = True
        
        curses.flushinp()
        self.stdscr.refresh()


    def handle_resize(self):
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # recalculate terminal dimensions
        self.mainwin_hfactor = max(1, (self.screen_h - 2) // 6)
        self.mainwin_wfactor = max(1, (self.screen_w - 2) // 7)
        self.mainwin_h = self.mainwin_hfactor * 6 + 1
        self.mainwin_w = self.mainwin_wfactor * 7 + 1

        self.promptwin_y = min(self.mainwin_h, self.screen_h - 1)
        self.promptwin_w = self.screen_w
        self.promptwin_h = 1
        self.promptwin_x = 0
        self.mainwin_y = 0
        self.mainwin_x = 0

        # rebuild windows
        del self.mainwin
        del self.promptwin
        self.init_windows()

        # make sure curses doesn't mix old pending input or queued screen updates
        curses.flushinp()
        self.redraw = True
        draw_screen(self)


    @property
    def selected_subcal(self):
        return self.subcalendars[self.selected_subcal_index]


    @property
    def selected_task(self):
        tasks = self.get_tasks_for_selected_day()
        if not tasks:
            return None
        return tasks[self.selected_task_index % len(tasks)][1]


    def month_has_changed(self, new_date):
        return (new_date.month != self.selected_date.month) or (new_date.year != self.selected_date.year)


    def get_tasks_for_selected_day(self):
        tasks = []
        for cal in self.subcalendars:
            if cal.hidden:
                continue
            for a in cal.tasks:
                if (a.year, a.month, a.day) == (self.selected_date.year, self.selected_date.month, self.selected_date.day):
                    tasks.append((cal, a))
        return tasks


    def clamp_task_index(self):
        tasks = self.get_tasks_for_selected_day()
        if tasks:
            max_idx = len(tasks) - 1
            self.selected_task_index = min(self.selected_task_index, max_idx)
        else:
            self.selected_task_index = 0
            self.task_scroll_offset = 0


    def change_date(self, new_date, motion=0):
        if self.month_has_changed(new_date):
            self.redraw = True

        self.last_selected_date = self.selected_date
        self.selected_date = new_date
        self.selected_task_index = 0
        self.task_scroll_offset = 0
        self.clamp_task_index()

        self.last_motion = f"{'+' if motion > 0 else ''}{motion}"
        self.count_buffer = ""


    def main_loop(self):
        while self.running:
            draw_screen(self)
            key = handle_key(self)
            normal_mode_input(self, key)
