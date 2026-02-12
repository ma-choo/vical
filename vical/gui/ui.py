# ui.py - Curses UI instance.
# This file is part of vical.
# License: MIT (see LICENSE)

import curses

from vical.editor.editor import Mode
from vical.enums.view import View
from vical.input import keys
from vical.input.normal import normal_input
from vical.input.prompt import prompt_input
from vical.input.visual import visual_input
from vical.input.operator import operator_pending_input
from vical.theme.manager import ThemeManager
from vical.gui.draw import draw_screen


class CursesUI:
    CAL_ROWS = 6
    CAL_COLS = 7
    STATUS_ROWS = 1
    PROMPT_ROWS = 1
    CAL_BORDERS = 2

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # mainwin - 6x7 calendar grid
        # subtract prompt row and curses box() borders to get usable mainwin space
        usable_h = self.screen_h - self.PROMPT_ROWS - self.CAL_BORDERS
        usable_w = self.screen_w - self.CAL_BORDERS

        # calculate height and width factors for drawing calendar grid and day cells
        self.mainwin_hfactor = max(1, usable_h // self.CAL_ROWS)
        self.mainwin_wfactor = max(1, usable_w // self.CAL_COLS)

        # calculate total mainwin dimensions from height and width factors
        # +1 to restore the right and bottom borders
        self.mainwin_h = self.mainwin_hfactor * self.CAL_ROWS + 1
        self.mainwin_w = self.mainwin_wfactor * self.CAL_COLS + 1
        self.mainwin_y = 0
        self.mainwin_x = 0

        # promptwin - single full-width line under mainwin
        self.statuswin_h = self.STATUS_ROWS
        self.statuswin_w = self.screen_w
        self.statuswin_y = self.mainwin_h # under mainwin
        self.statuswin_x = 0

        # promptwin - single full-width line under statuswin
        self.promptwin_h = self.PROMPT_ROWS
        self.promptwin_w = self.screen_w
        self.promptwin_y = self.mainwin_h # + 1 # under statuswin # under mainwin
        self.promptwin_x = 0

        # TODO: this should not be here. it should be in mainwin once we make it a widget object that handles itself
        self.day_cell_scroll_offset = 0

        self.theme = ThemeManager(self.stdscr)

        self.layout_update = True
        self.need_redraw = True

        self.init_windows()
        self.stdscr.refresh()

    def init_windows(self):
        self.mainwin = curses.newwin(self.mainwin_h, self.mainwin_w, self.mainwin_y, self.mainwin_x)
        self.promptwin = curses.newwin(self.promptwin_h, self.promptwin_w, self.promptwin_y, self.promptwin_x)

    def handle_resize(self):
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # recompute usable space
        usable_h = self.screen_h - self.PROMPT_ROWS - self.CAL_BORDERS
        usable_w = self.screen_w - self.CAL_BORDERS

        # recalc mainwin scaling factors
        self.mainwin_hfactor = max(1, usable_h // self.CAL_ROWS)
        self.mainwin_wfactor = max(1, usable_w // self.CAL_COLS)

        # recalc mainwin dimensions
        self.mainwin_h = self.mainwin_hfactor * self.CAL_ROWS + 1
        self.mainwin_w = self.mainwin_wfactor * self.CAL_COLS + 1
        self.mainwin_y = 0
        self.mainwin_x = 0

        # recalc promptwin
        self.promptwin_h = self.PROMPT_ROWS
        self.promptwin_w = self.screen_w
        self.promptwin_y = min(self.mainwin_h, self.screen_h - self.PROMPT_ROWS)
        self.promptwin_x = 0

        # reinitialize windows
        del self.mainwin
        del self.promptwin
        self.init_windows()

        curses.flushinp()
        self.layout_update = True

        self.request_redraw()
        self.need_redraw = True

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
                    case Mode.PROMPT:
                        prompt_input(self, editor, key)
                    case Mode.VISUAL:
                        normal_input(editor, key)
                    case Mode.OPERATOR_PENDING:
                        operator_pending_input(editor, key)

        except SystemExit:
            self.stdscr.clear()
            self.stdscr.refresh()
            raise

    # TODO: these should move to CalendarModule once we implement that
    def get_scroll_offset(self, num_items, max_visible, selected_index):
        offset = self.day_cell_scroll_offset

        if selected_index >= 0:
            if selected_index >= offset + max_visible:
                offset = selected_index - max_visible + 1
            elif selected_index < offset:
                offset = selected_index
            offset = max(0, min(offset, max(0, num_items - max_visible)))

        self.day_cell_scroll_offset = offset
        return offset

    def _update_editor_layout(self, editor):
        if editor.settings.view == View.WEEKLY:
            editor.max_items_visible = max(0, self.mainwin_hfactor - self.CAL_BORDERS)
        elif editor.settings.view == View.MONTHLY:
            editor.max_items_visible = max(0, self.mainwin_h - self.CAL_BORDERS)
        editor.redraw = True
        self.layout_update = False