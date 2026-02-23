# License: MIT (see LICENSE)

"""
Drawing functions for curses UI.
"""

import calendar
import curses
from datetime import date, timedelta

from vical.core.subcalendar import Task, Event
from vical.settings import View


# Layout constants for drawing day cells:
CELL_INSET_Y = 1
CELL_INSET_X = 1
DAY_HEADER_ROWS = 1
CELL_RIGHT_PADDING = 2
CELL_BORDER_THICKNESS = 1
SELECTION_MARKER = ">"
TASK_COMPLETED_MARKER = "󰄳 "
TASK_UNCOMPLETED_MARKER = "󰄰 "
EVENT_RIBBON_START = ""
EVENT_RIBBON_END = ""
SCROLL_INDICATOR_UP = '▲'
SCROLL_INDICATOR_DOWN = '▼'


def draw_screen(ui):
    """
    Render the entire screen.
    """
    e = ui.editor

    # TODO clamp
    sel_start, sel_end = _get_selection_range(ui)

    if e.last_visual_anchor_date is not None:
        old_start = min(e.last_visual_anchor_date, e.last_selected_date)
        old_end   = max(e.last_visual_anchor_date, e.last_selected_date)
    else:
        old_start = old_end = e.last_selected_date

    # Full redraw
    if e.status.need_redraw:
        if e.settings.view == View.MONTH:
            _draw_full_month(ui)

        ui.stdscr.refresh()

        e.status.need_redraw = False
        e.status.redraw_counter += 1

    # Partial redraw
    else:
        redraw_start = min(old_start, sel_start)
        redraw_end   = max(old_end, sel_end)

        d = redraw_start
        while d <= redraw_end:
            _draw_day_cell(ui, d)
            d += timedelta(days=1)
    
    _draw_prompt_status(ui)

    ui.mainwin.noutrefresh()
    ui.promptwin.noutrefresh()
    curses.doupdate()

    # Snapshot selection state for next frame
    e.last_selected_date = e.selected_date
    e.last_visual_anchor_date = e.visual_anchor_date

def _draw_day_cell(ui, cell_date: date):
    e = ui.editor

    if e.settings.view == View.MONTH:
        _draw_day_cell_monthly(ui, cell_date)


def _draw_full_month(ui):
    """
    Draw a full 6x7 grid of day cells to represent a full monthly calendar.
    """
    e = ui.editor

    _draw_calendar_base(ui)
    first_of_month = e.selected_date.replace(day=1)

    # Last sunday before the first day of the month
    start_date = _get_start_of_week(ui, first_of_month)
    e.first_visible_date = start_date

    # draw 42 days (6 weeks)
    for i in range(42):
        d = start_date + timedelta(days=i)
        _draw_day_cell_monthly(ui, d)


def _draw_calendar_base(ui):
    """
    Draw static calendar elements
    (grid lines, day headers, month footer).
    """
    CELL_TEXT_PADDING_X = 1
    FOOTER_RIGHT_PADDING = 2
    FOOTER_LEFT_PADDING = 1
    e = ui.editor

    ui.mainwin.erase()

    # grid lines 
    if e.settings.view == View.MONTH:
        # 6x7 rows/columns
        for y in range(1, 6):
            ui.mainwin.hline(ui.mainwin_hfactor * y, 0, curses.ACS_HLINE, ui.mainwin_w)
        for x in range(1, 7):
            ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    elif e.settings.view == View.WEEK:
        for x in range(1, 7):
            ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    ui.mainwin.box()

    # day name headers
    for x in range(7):
        ui.mainwin.addstr(
            0,
            x * ui.mainwin_wfactor + CELL_TEXT_PADDING_X,
            _get_day_name(ui, x)[:ui.mainwin_wfactor - CELL_TEXT_PADDING_X]
        )

    # month footer with month name and year
    footer_str = f"{_get_month_name(e.selected_date.month)}-{e.selected_date.year}"
    footer_x = max(0, ui.mainwin_w - FOOTER_RIGHT_PADDING - len(footer_str))
    try:
        ui.mainwin.addstr(ui.mainwin_h - FOOTER_LEFT_PADDING, footer_x, footer_str)
    except curses.error:
        pass


def _draw_day_cell_monthly(ui, cell_date: date):
    e = ui.editor
    theme = ui.theme

    today = date.today()
    selected_date = e.selected_date

    idx = (cell_date - e.first_visible_date).days
    pos_y = (idx // 7) * ui.mainwin_hfactor + CELL_INSET_Y
    pos_x = (idx % 7) * ui.mainwin_wfactor + CELL_INSET_X
    base_y = pos_y + DAY_HEADER_ROWS
    arrow_x = pos_x + ui.mainwin_wfactor - CELL_RIGHT_PADDING

    cell_w = ui.mainwin_wfactor - CELL_BORDER_THICKNESS
    cell_h = ui.mainwin_hfactor - CELL_BORDER_THICKNESS

    # clear cell
    for r in range(cell_h):
        try:
            ui.mainwin.addstr(pos_y + r, pos_x, " " * cell_w)
        except curses.error:
            pass

    # day number
    attr = 0
    if cell_date.month != selected_date.month:
        attr |= curses.color_pair(theme.pair("dim"))
    if cell_date == today:
        attr |= curses.color_pair(theme.pair("today"))
    # highlight selected day
    start, end = _get_selection_range(ui)
    if start <= cell_date <= end:
        attr = curses.A_REVERSE

    try:
        ui.mainwin.attron(attr)
        ui.mainwin.addstr(pos_y, pos_x, f"{cell_date.day:>{cell_w}}")
        ui.mainwin.attroff(attr)
    except curses.error:
        pass

    # collect items
    items = []
    for cal in e.subcalendars:
        if cal.hidden:
            continue
        for item in cal.items:
            if item.occurs_on(cell_date):
                items.append((cal, item))

    max_items_visible = cell_h - DAY_HEADER_ROWS
    selected_index = e.selected_item_index if cell_date == selected_date else -1
    scroll_offset = ui.get_scroll_offset(
        num_items=len(items),
        max_visible=max_items_visible,
        selected_index=selected_index
    ) if cell_date == selected_date else 0
    visible = items[scroll_offset:scroll_offset + max_items_visible]

    def item_is_selected(i):
        return (scroll_offset + i) == selected_index

    # draw items
    for i, (cal, item) in enumerate(visible):
        y = base_y + i

        # ---- EVENTS ----
        if isinstance(item, Event):
            base_attr = curses.color_pair(theme.pair(cal.color)) | curses.A_REVERSE

            is_selected = (cell_date == selected_date and item_is_selected(i))
            text_x = pos_x + (len(SELECTION_MARKER) if is_selected else 0)
            text_w = cell_w - (text_x - pos_x)

            # background ribbon
            try:
                ui.mainwin.attron(base_attr)
                ui.mainwin.addstr(y, pos_x, " " * cell_w)
                ui.mainwin.attroff(base_attr)
            except curses.error:
                pass

            # ribbon text
            if _is_event_text_visible(ui, cell_date, item):
                if cell_date == item.start_date or is_selected:
                    event_text = f"{EVENT_RIBBON_START} {item.name}"
                else:
                    event_text = f" {item.name}"

                try:
                    ui.mainwin.attron(base_attr)
                    ui.mainwin.addstr(y, text_x, event_text[:text_w])
                    ui.mainwin.attroff(base_attr)
                except curses.error:
                    pass

            # ribbon end cap (no reverse)
            if cell_date == item.end_date:
                end_attr = curses.color_pair(theme.pair(cal.color))
                end_x = pos_x + cell_w - len(EVENT_RIBBON_END)
                try:
                    ui.mainwin.attron(end_attr)
                    ui.mainwin.addstr(y, end_x, EVENT_RIBBON_END)
                    ui.mainwin.attroff(end_attr)
                except curses.error:
                    pass

            if is_selected:
                try:
                    ui.mainwin.addstr(y, pos_x, SELECTION_MARKER)
                except curses.error:
                    pass

        # ---- TASKS ----
        elif isinstance(item, Task):
            attr = 0
            marker = TASK_UNCOMPLETED_MARKER
            label=""
            if cell_date == item.deadline:
                    attr = curses.color_pair(theme.pair("deadline"))
                    label = "Due:"
            else:
                attr = curses.color_pair(theme.pair(cal.color))

            if item.completed:
                attr = curses.color_pair(theme.pair("dim"))
                marker = TASK_COMPLETED_MARKER


            task_text = f"{marker}{label}{item.name}"

            draw_x = pos_x
            if cell_date == selected_date and item_is_selected(i):
                try:
                    ui.mainwin.addstr(y, pos_x, SELECTION_MARKER)
                except curses.error:
                    pass
                draw_x += len(SELECTION_MARKER)

            try:
                ui.mainwin.attron(attr)
                ui.mainwin.addstr(y, draw_x, task_text[:cell_w - (draw_x - pos_x)])
                ui.mainwin.attroff(attr)
            except curses.error:
                pass

    # scroll indicators
    try:
        if scroll_offset > 0:
            ui.mainwin.addstr(base_y, arrow_x, SCROLL_INDICATOR_UP)
        if scroll_offset + max_items_visible < len(items):
            ui.mainwin.addstr(
                base_y + len(visible) - CELL_BORDER_THICKNESS,
                arrow_x,
                SCROLL_INDICATOR_DOWN
            )
    except curses.error:
        pass


def _get_day_name(ui, day: int) -> str:
    first_weekday = ui.editor.settings.week_start
    return calendar.day_abbr[(first_weekday + day) % 7]


def _get_month_name(month: int) -> str:
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    raise ValueError(f"Invalid month number: {month}")


def _get_start_of_week(ui, d: date) -> date:
    """
    Given a date, return the date of the first day of that week
    """
    first_weekday = ui.editor.settings.week_start
    delta = (d.weekday() - first_weekday) % 7
    return d - timedelta(days=delta)


def _get_first_visible_date(ui) -> date:
    """
    Compute the first visible date for drawing.
    """
    e = ui.editor

    if e.settings.view == View.MONTH:
        first_of_month = e.selected_date.replace(day=1)
        return _get_start_of_week(ui, first_of_month)
    elif e.settings.view == View.WEEK:
        return _get_start_of_week(ui, e.selected_date)


def _is_event_text_visible(ui, cell_date, item):
    e = ui.editor

    return (
        cell_date == e.selected_date or
        cell_date == item.start_date or
        cell_date.weekday() == e.settings.week_start
    )


# TODO: just replace this with editor.get_visual_selection_range
def _get_selection_range(ui):
    """
    Return (start, end) of the currently selected date range.
    - Normal mode: start == end == selected_date
    - Visual mode: anchor and selected_date define the range
    """
    e = ui.editor

    if e.visual_anchor_date is not None:
        start = min(e.visual_anchor_date, e.selected_date)
        end = max(e.visual_anchor_date, e.selected_date)
    else:
        start = end = e.selected_date
    return start, end


def _draw_prompt_status(ui):
    """
    Draw prompt/status line
    """
    e = ui.editor
    theme = ui.theme

    curses.curs_set(0)
    ui.promptwin.erase()
    
    msg, is_error = e.status.msg

    dirty = f"{'[+]' if e.dirty else ''}"
    pressed_keys = ui.keyparser.get_pending_keys()
    hidden = f"{'  [H]' if e.selected_subcal.hidden else ''}" # TODO: This will crash selected_subcal is ever none.

    status_prefix = f"{pressed_keys}  {dirty}  {hidden}"

    subcal_name = e.selected_subcal.name

    try:
        if ui.cmd_buffer:
            ui.promptwin.addstr(0, 0, f"{ui.cmd_buffer}")

        # display selected item if any
        item = e.selected_item
        if item:
            attr = curses.color_pair(theme.pair(item.parent_subcal.color))
            if isinstance(item, Event):
                attr |= curses.A_REVERSE
                ui.promptwin.attron(attr)
                ui.promptwin.addstr(0, 0, f"{EVENT_RIBBON_START} {item.name} ")
                ui.promptwin.attroff(attr)
                attr = curses.color_pair(theme.pair(item.parent_subcal.color))
                ui.promptwin.attron(attr)
                ui.promptwin.addstr(f"{EVENT_RIBBON_END}")
                ui.promptwin.attroff(attr)
            else:
                ui.promptwin.attron(attr)
                ui.promptwin.addstr(0, 0, item.name)
                ui.promptwin.attroff(attr)

        # draw uncolored part of status line
        # TODO: guard against right_x becoming negative
        right_x = ui.mainwin_w - (len(status_prefix) + len(subcal_name))
        ui.promptwin.addstr(0, right_x, status_prefix)

        # draw subcalendar name in its color
        attr = curses.color_pair(theme.pair(e.selected_subcal.color))
        ui.promptwin.attron(attr)
        ui.promptwin.addstr(0, right_x + len(status_prefix), subcal_name)
        ui.promptwin.attroff(attr)

    except Exception as err:
        attr = curses.color_pair(theme.pair("error"))
        ui.promptwin.attron(attr)
        ui.promptwin.addstr(0, 0, f"ERROR: {err}")
        ui.promptwin.attroff(attr)
