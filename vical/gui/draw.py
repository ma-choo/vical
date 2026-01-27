# draw.py - Calendar and prompt line drawing functions for Curses UI instance.
# This file is part of vical.
# License: MIT (see LICENSE)

import curses
import calendar
from datetime import date, timedelta
from vical.core.editor import Mode


def _attron(win, theme, color):
    win.attron(curses.color_pair(theme.pair(color)))


def _attroff(win, theme, color):
    win.attroff(curses.color_pair(theme.pair(color)))


def _get_day_name(day):
    return calendar.day_abbr[(day + 6) % 7]  # shift so sunday = 0


def _get_month_name(month):
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    raise ValueError(f"Invalid month number: {month}")


def update_promptwin(ui, text):
    ui.promptwin.erase()
    ui.promptwin.addstr(0, 0, text)
    ui.promptwin.noutrefresh()
    curses.doupdate()


def _draw_prompt_status(ui, editor, theme):
    """
    Draw prompt/status line
    """
    msg, is_error = editor.msg
    curses.curs_set(0)
    # build the status line
    status_prefix = (
        f"{'[+]' if editor.modified else ''}"
        f"{f'  {editor.operator} ' if editor.operator else ' '}"
        f"{f'  {editor.count}' if editor.count else ''}"
        f"{f'  {editor.mode} ' if not editor.mode == Mode.NORMAL else ' '}"
        f"  {editor.view}"
        # f"  {editor.mode}"
        f"  {editor.last_motion}"
        f"{f' {editor.saved_state_id[:4]} {editor.state_id[:4]}' if editor.debug else ''}"
        f"{f'  {editor.redraw} {editor.redraw_counter}' if editor.debug else ''}"
        f"  {'[H]' if editor.selected_subcal.hidden else ''}"
    )

    subcal_name = editor.selected_subcal.name
    ui.promptwin.erase()

    try:
        # display selected task if any
        if editor.selected_task:
            ui.promptwin.addstr(0, 0, editor.selected_task.name)
        else:
            if is_error:
                _attron(ui.promptwin, theme, "error")
                ui.promptwin.addstr(0, 0, f"ERROR: {msg}")
                _attroff(ui.promptwin, theme, "error")
            else:
                ui.promptwin.addstr(0, 0, msg)

        # draw uncolored part of status line
        right_x = ui.mainwin_w - (len(status_prefix) + len(subcal_name))
        ui.promptwin.addstr(0, right_x, status_prefix)

        # draw subcalendar name in its color
        _attron(ui.promptwin, theme, editor.selected_subcal.color)
        ui.promptwin.addstr(0, right_x + len(status_prefix), subcal_name)
        _attroff(ui.promptwin, theme, editor.selected_subcal.color)

    except Exception as e:
        _attron(ui.promptwin, theme, "error")
        ui.promptwin.addstr(0, 0, f"ERROR: {e}")
        _attroff(ui.promptwin, theme, "error")


def _draw_calendar_base(ui, editor):
    """
    Draw static calendar elements
    (grid lines, day headers, month footer).
    """
    CELL_TEXT_PADDING_X = 1
    FOOTER_RIGHT_PADDING = 2
    FOOTER_LEFT_PADDING = 1

    ui.mainwin.erase()

    # grid lines (6x7 rows/columns)
    for y in range(1, 6):
        ui.mainwin.hline(ui.mainwin_hfactor * y, 0, curses.ACS_HLINE, ui.mainwin_w)
    for x in range(1, 7):
        ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    ui.mainwin.box()

    # day name headers
    for x in range(7):
        try:
            ui.mainwin.addstr(0, x * ui.mainwin_wfactor + CELL_TEXT_PADDING_X,
                              _get_day_name(x)[:ui.mainwin_wfactor - CELL_TEXT_PADDING_X])
        except curses.error:
            pass

    # month footer with month name and year
    footer_str = f"{_get_month_name(editor.selected_date.month)}-{editor.selected_date.year}"
    footer_x = max(0, ui.mainwin_w - FOOTER_RIGHT_PADDING - len(footer_str))
    try:
        ui.mainwin.addstr(ui.mainwin_h - FOOTER_LEFT_PADDING, footer_x, footer_str)
    except curses.error:
        pass


def _draw_day_cell(ui, editor, cell_date, theme):
    """
    Draw a single day cell with
    - day numbers
    - current date and date selection
    - tasks and task selection
    - scroll indicators
    """
    CELL_INSET_Y = 1
    CELL_INSET_X = 1
    DAY_HEADER_ROWS = 1
    CELL_RIGHT_PADDING = 2
    CELL_BORDER_THICKNESS = 1
    COMPLETION_MARK_WIDTH = 2

    today = date.today()
    selected_date = editor.selected_date

    # calculate cell index relative to first visible date
    idx = (cell_date - editor.first_visible_date).days
    pos_y = (idx // 7) * ui.mainwin_hfactor + CELL_INSET_Y
    pos_x = (idx % 7) * ui.mainwin_wfactor + CELL_INSET_X
    base_y = pos_y + DAY_HEADER_ROWS
    arrow_x = pos_x + ui.mainwin_wfactor - CELL_RIGHT_PADDING

    cell_w = ui.mainwin_wfactor - CELL_BORDER_THICKNESS
    cell_h = ui.mainwin_hfactor - CELL_BORDER_THICKNESS

    # 1. clear cell area
    for r in range(cell_h):
        try:
            ui.mainwin.addstr(pos_y + r, pos_x, " " * cell_w)
        except curses.error:
            pass

    # 2. draw day numbers
    attr = 0
    if cell_date.month != selected_date.month:
        attr |= curses.color_pair(theme.pair("dim")) # dim day numbers outside selected month
    else:
        if cell_date == today:
            attr |= curses.color_pair(theme.pair("today")) # highlight current date
        if cell_date == selected_date:
            attr |= curses.A_REVERSE # highlight selected date
    try:
        ui.mainwin.attron(attr)
        ui.mainwin.addstr(pos_y, pos_x, f"{cell_date.day:>{cell_w}}") # draw day number at top right corner of day cell
        ui.mainwin.attroff(attr)
    except curses.error:
        pass

    # 3. draw tasks
    max_per_day = ui.mainwin_hfactor - (DAY_HEADER_ROWS + CELL_BORDER_THICKNESS)
    tasks = []
    for cal in editor.subcalendars:
        if cal.hidden:
            continue
        for t in cal.tasks:
            if t.date == cell_date:
                tasks.append((cal, t))

    scroll_offset = editor.task_scroll_offset if cell_date == selected_date else 0
    visible = tasks[scroll_offset:scroll_offset + max_per_day]
    selected_index = editor.selected_task_index if cell_date == selected_date else -1

    for i, (cal, t) in enumerate(visible):
        y = base_y + i
        attr = curses.color_pair(theme.pair(cal.color)) # color the task with its subcalendar color
        # completion markers
        text = f"{'✓ ' if t.completed else ''}{t.name[:cell_w - (COMPLETION_MARK_WIDTH if t.completed else 0)]}"
        if cell_date == selected_date and (scroll_offset + i) == selected_index:
            attr |= curses.A_REVERSE # highlight selected task

        try:
            ui.mainwin.attron(attr)
            ui.mainwin.addstr(y, pos_x, text)
            ui.mainwin.attroff(attr)
        except curses.error:
            pass

    # 4. draw scroll indicators
    try:
        if scroll_offset > 0:
            ui.mainwin.addstr(base_y, arrow_x, "▲")
        if scroll_offset + max_per_day < len(tasks):
            ui.mainwin.addstr(base_y + len(visible) - CELL_BORDER_THICKNESS, arrow_x, "▼")
    except curses.error:
        pass


def _draw_full_grid(ui, editor, theme):
    """
    Draw a full 6x7 grid of day cells to represent a visual calendar.
    """
    _draw_calendar_base(ui, editor)
    first_of_month = editor.selected_date.replace(day=1)

    # last sunday before the first day of the month
    offset = (first_of_month.weekday() + 1) % 7  # mon=0 sun=6
    start_date = first_of_month - timedelta(days=offset)
    editor.first_visible_date = start_date

    # draw 42 days (6 weeks)
    for i in range(42):
        d = start_date + timedelta(days=i)
        _draw_day_cell(ui, editor, d, theme)


def draw_screen(ui, editor, theme):
    """
    Render the entire screen.
    Performs a full redraw when required, otherwise updates only affected day cells.
    """
    if editor.redraw:
        _draw_full_grid(ui, editor, theme)
        editor.redraw_counter += 1
        ui.stdscr.refresh()
        editor.last_selected_date = editor.selected_date
    else:
        # redraw only necessary day cells
        if editor.last_selected_date != editor.selected_date:
            _draw_day_cell(ui, editor, editor.last_selected_date, theme)
        _draw_day_cell(ui, editor, editor.selected_date, theme)

    if editor.mode is Mode.PROMPT and editor.prompt:
        update_promptwin(ui, editor.prompt["label"] + editor.prompt["user_input"])
    else:
        _draw_prompt_status(ui, editor, theme)

    ui.mainwin.noutrefresh()
    ui.promptwin.noutrefresh()
    curses.doupdate()
    
    editor.redraw = False
    ui.redraw = False
