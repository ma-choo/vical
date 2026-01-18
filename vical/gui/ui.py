# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from vical.core.editor import Mode
from vical.input import keys
from vical.input.normal import normal_input
from vical.input.prompt import prompt_input
from vical.input.command import command_input
from vical.input.operator import operator_pending_input
from vical.gui.colors import Colors
from vical.gui.draw import draw_screen


class CursesUI:
    def __init__(self, stdscr):
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

        self.custom_colors = []

        self.redraw = True

        self.init_colors()
        self.init_windows()
        self.stdscr.refresh()

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()

        if not curses.has_colors():
            return

        if curses.can_change_color():
            def rgb(r, g, b):
                return int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255)

            BASE = 20
            BG, FG, COMMENT, PURPLE, RED, CYAN, YELLOW, GREEN, PINK = range(BASE, BASE + 9)

            curses.init_color(BG, *rgb(40, 42, 54))
            curses.init_color(FG, *rgb(248, 248, 242))
            curses.init_color(COMMENT, *rgb(98, 114, 164))
            curses.init_color(PURPLE, *rgb(189, 147, 249))
            curses.init_color(RED, *rgb(255, 85, 85))
            curses.init_color(CYAN, *rgb(139, 233, 253))
            curses.init_color(YELLOW, *rgb(241, 250, 140))
            curses.init_color(GREEN, *rgb(80, 250, 123))
            curses.init_color(PINK, *rgb(255, 121, 198))

            curses.init_pair(1, RED, BG) # error
            curses.init_pair(2, FG, COMMENT) # today
            curses.init_pair(3, COMMENT, BG) # dim
            curses.init_pair(4, RED, BG)
            curses.init_pair(5, CYAN, BG)
            curses.init_pair(6, YELLOW, BG)
            curses.init_pair(7, GREEN, BG)
            curses.init_pair(8, PINK, BG)

        else:
            # fallback
            curses.init_pair(1, curses.COLOR_RED, -1) # error
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE) # today
            curses.init_pair(3, curses.COLOR_BLUE, -1) # dim
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_CYAN, -1)
            curses.init_pair(7, curses.COLOR_YELLOW, -1)
            curses.init_pair(8, curses.COLOR_GREEN, -1)


    def init_colors_old(self):
        curses.start_color()
        curses.use_default_colors()
        """
        curses.init_pair(1, curses.COLOR_RED, -1) # error
        curses.init_pair(2, -1, curses.COLOR_WHITE) # selection
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE) # current date highlight
        curses.init_pair(4, curses.COLOR_BLUE, -1) # dim
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        curses.init_pair(7, curses.COLOR_CYAN, -1)
        curses.init_pair(8, curses.COLOR_YELLOW, -1)
        curses.init_pair(9, curses.COLOR_GREEN, -1)
        curses.init_pair(10, curses.COLOR_BLUE, -1)
        """
        if curses.can_change_color():
            curses.init_color(8,  40,  42,  54)  # bg
            curses.init_color(9,  248, 248, 242) # fg
            curses.init_color(10, 98,  114, 164) # comment
            curses.init_color(11, 189, 147, 249) # purple
            curses.init_color(12, 255, 85, 85)   # red
            curses.init_color(13, 139, 233, 253) # cyan
            curses.init_color(14, 241, 250, 140) # yellow
            curses.init_color(15, 80, 250, 123) # green
            curses.init_color(16, 80, 250, 123) # pink
            curses.init_pair(1, 12, 8)
            curses.init_pair(2, 8, 9)
            curses.init_pair(3, 10, 11)
            curses.init_pair(4, 10, 8)
            curses.init_pair(5, 11, 8)
            curses.init_pair(6, 12, 8)
            curses.init_pair(7, 13, 8)
            curses.init_pair(8, 14, 8)
            curses.init_pair(9, 15, 8)
            curses.init_pair(10, 16, 8)
        else:
            curses.init_pair(1, curses.COLOR_RED, -1) # error
            curses.init_pair(2, -1, curses.COLOR_WHITE) # selection
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE) # current date highlight
            curses.init_pair(4, curses.COLOR_BLUE, -1) # dim
            curses.init_pair(5, curses.COLOR_RED, -1)
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            curses.init_pair(7, curses.COLOR_CYAN, -1)
            curses.init_pair(8, curses.COLOR_YELLOW, -1)
            curses.init_pair(9, curses.COLOR_GREEN, -1)
            curses.init_pair(10, curses.COLOR_BLUE, -1)

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

    def main(self, editor):
        try:
            while True:
                draw_screen(self, editor)
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
