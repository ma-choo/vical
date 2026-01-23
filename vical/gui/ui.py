# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from vical.core.editor import Mode
from vical.input import keys
from vical.input.normal import normal_input
from vical.input.prompt import prompt_input
from vical.input.command import command_input
from vical.input.operator import operator_pending_input
from vical.theme.manager import ThemeManager
from vical.gui.draw import draw_screen


class CursesUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # mainwin: 6 rows x 7 columns calendar grid
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

        self.theme = ThemeManager(self.stdscr)

        self.layout_update = True

        self.init_windows()
        self.stdscr.refresh()

    def init_windows(self):
        self.mainwin = curses.newwin(self.mainwin_h, self.mainwin_w, self.mainwin_y, self.mainwin_x)
        self.promptwin = curses.newwin(self.promptwin_h, self.promptwin_w, self.promptwin_y, self.promptwin_x)

    def handle_resize(self):
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # recalc mainwin
        self.mainwin_hfactor = max(1, (self.screen_h - 2) // 6)
        self.mainwin_wfactor = max(1, (self.screen_w - 2) // 7)
        self.mainwin_h = self.mainwin_hfactor * 6 + 1
        self.mainwin_w = self.mainwin_wfactor * 7 + 1

        # recalc promptwin
        self.promptwin_y = min(self.mainwin_h, self.screen_h - 1)
        self.promptwin_w = self.screen_w
        self.promptwin_h = 1
        self.promptwin_x = 0
        self.mainwin_y = 0
        self.mainwin_x = 0

        # reinitialize windows
        del self.mainwin
        del self.promptwin
        self.init_windows()

        # flush input
        curses.flushinp()
        self.redraw = True

    def _update_editor_layout(self, editor):
        editor.max_tasks_visible = max(0, self.mainwin_hfactor - 2)
        editor.redraw = True

    def main(self, editor):
        try:
            while True:
                if self.layout_update:
                    self._update_editor_layout(editor)
                draw_screen(self, editor, self.theme)
                key = keys.handle_key(self)
                match editor.mode:
                    case Mode.NORMAL:
                        normal_input(editor, key)
                    case Mode.COMMAND:
                        command_input(self, editor, key)
                    case Mode.PROMPT:
                        prompt_input(self, editor, key)
                    case Mode.OPERATOR_PENDING:
                        operator_pending_input(editor, key)

        except SystemExit:
            self.stdscr.clear()
            self.stdscr.refresh()
            raise
