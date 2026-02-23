# License: MIT (see LICENSE)

"""
Curses UI handling.
"""

import curses

from vical.gui.draw import draw_screen
from vical.input.keyparser import KeyParser
from vical.theme.manager import ThemeManager


class CursesUI:
    CAL_ROWS = 6
    CAL_COLS = 7
    STATUS_ROWS = 1
    PROMPT_ROWS = 1
    CAL_BORDERS = 2

    def __init__(self, stdscr, editor):
        self.stdscr = stdscr
        self.editor = editor
        self.keyparser = KeyParser(self)
        self.theme = ThemeManager(self.stdscr)

        self.cmd_buffer = "This should show if all is well"
        
        # TODO: this should not be here. it should be in mainwin once we make it a widget object that handles itself
        self.day_cell_scroll_offset = 0

        self.init_windows()
        self.stdscr.refresh()

    def init_windows(self):
        # Get current terminal dimensions
        self.screen_h, self.screen_w = self.stdscr.getmaxyx()

        # mainwin: 6x7 calendar grid
        # Subtract prompt row and curses box() borders to get usable mainwin space
        usable_h = self.screen_h - self.PROMPT_ROWS - self.CAL_BORDERS
        usable_w = self.screen_w - self.CAL_BORDERS

        # Calculate height and width factors for drawing calendar grid and day cells
        self.mainwin_hfactor = max(1, usable_h // self.CAL_ROWS)
        self.mainwin_wfactor = max(1, usable_w // self.CAL_COLS)

        # Calculate total mainwin dimensions from height and width factors
        # +1 to restore the right and bottom borders
        self.mainwin_h = self.mainwin_hfactor * self.CAL_ROWS + 1
        self.mainwin_w = self.mainwin_wfactor * self.CAL_COLS + 1
        self.mainwin_y = 0
        self.mainwin_x = 0

        # statuswin: Single full-width line under mainwin
        # self.statuswin_h = self.STATUS_ROWS
        # self.statuswin_w = self.screen_w
        # self.statuswin_y = self.mainwin_h # under mainwin
        # self.statuswin_x = 0

        # promptwin - Single full-width line under mainwin TODO move under statuswin
        self.promptwin_h = self.PROMPT_ROWS
        self.promptwin_w = self.screen_w
        self.promptwin_y = self.mainwin_h # Under mainwin
        self.promptwin_x = 0

        self.mainwin = curses.newwin(self.mainwin_h, self.mainwin_w, self.mainwin_y, self.mainwin_x)
        self.promptwin = curses.newwin(self.promptwin_h, self.promptwin_w, self.promptwin_y, self.promptwin_x)

    def handle_resize(self):
        """
        Handle resize event.
        """
        del self.mainwin
        del self.promptwin

        self.init_windows()

        curses.flushinp()
        self.editor.status.request_redraw()

    def handle_key(self, key):
        """
        Handle keypress.
        """
        if key == curses.KEY_RESIZE:
            self.handle_resize()
        else:
            self.keyparser.feed(key)

    def main(self):
        try:
            while True:
                draw_screen(self)
                pressed = self.stdscr.getch()
                self.handle_key(pressed)

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