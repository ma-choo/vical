# This file is part of vical.
# License: MIT (see LICENSE)

import curses
import calendar
from datetime import date, datetime, timedelta
from vical.core.editor import Mode
from vical.gui.colors import Colors


def _get_day_name(index: int) -> str:
    return calendar.day_abbr[(index + 6) % 7] # shift so sunday = 0


def _get_month_name(month: int) -> str:
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    else:
        raise ValueError(f"Invalid month number: {month}")


def update_promptwin(ui, text):
    ui.promptwin.erase()
    ui.promptwin.addstr(0, 0, text)
    ui.promptwin.noutrefresh()
    curses.doupdate()


def _draw_prompt_status(ui, editor):
    msg, is_error = editor.msg
    curses.curs_set(0)

    status_prefix = (
        f"{'[+]' if editor.modified else ''}" # modified marker
        f"{f'  {editor.operator} ' if editor.operator else ' '}" # operator
        f"{f'  {editor.count}' if editor.count else ''}" # count
        f"  {editor.mode}" # mode
        f"  {editor.last_motion}" # motion
        f"{f' {editor.saved_state_id[:4]} {editor.state_id[:4]}' if editor.debug else ''}" # state hash
        f"{f'  {editor.redraw} {editor.redraw_counter}' if editor.debug else ''}"  # redraw counter
        f"  {'[H]' if editor.selected_subcal.hidden else ''}"  # hidden flag
    )

    subcal_name = editor.selected_subcal.name
    ui.promptwin.erase()

    try:
        # display selected task if any
        if editor.selected_task:
            ui.promptwin.addstr(0, 0, editor.selected_task.name)
        else:
            if is_error:
                ui.promptwin.attron(curses.color_pair(Colors.ERROR))  # red
                ui.promptwin.addstr(0, 0, f"ERROR: {msg}")
                ui.promptwin.attroff(curses.color_pair(Colors.ERROR))
            else:
                ui.promptwin.addstr(0, 0, msg)

        # draw the uncolored part of the status line
        right_x = ui.mainwin_w - (len(status_prefix) + len(subcal_name))
        ui.promptwin.addstr(0, right_x, status_prefix)

        # draw the subcalendar name in its color
        ui.promptwin.attron(curses.color_pair(editor.selected_subcal.color))
        ui.promptwin.addstr(0, right_x + len(status_prefix), subcal_name)
        ui.promptwin.attroff(curses.color_pair(editor.selected_subcal.color))

    except Exception as e:
        ui.promptwin.attron(curses.color_pair(Colors.ERROR))
        ui.promptwin.addstr(0, 0, f"ERROR: {e}")
        ui.promptwin.attroff(curses.color_pair(Colors.ERROR))



# draw static calendar elements (grid lines, day headers, month footer)
def _draw_calendar_base(ui, editor):
    ui.mainwin.erase()

    # grid lines
    for y in range(1, 6):
        ui.mainwin.hline(ui.mainwin_hfactor * y, 0, curses.ACS_HLINE, ui.mainwin_w)
    for x in range(1, 7):
        ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    ui.mainwin.box()

    # day headers
    for x in range(7):
        try:
            ui.mainwin.addstr(0, x * ui.mainwin_wfactor + 1,
                              _get_day_name(x)[:ui.mainwin_wfactor - 1])
        except curses.error:
            pass

    # month footer
    footer_str = f"{_get_month_name(editor.selected_date.month)}-{editor.selected_date.year}"
    footer_x = max(0, ui.mainwin_w - 2 - len(footer_str))
    try:
        ui.mainwin.addstr(ui.mainwin_h - 1, footer_x, footer_str)
    except curses.error:
        pass



# draw a single day cell (number, tasks, highlights)
def _draw_day_cell(ui, editor, year, month, day):
    today = date.today()
    selected = editor.selected_date

    # calculate cell index relative to first visible date
    idx = (date(year, month, day) - editor.first_visible_date).days
    pos_y = (idx // 7) * ui.mainwin_hfactor + 1
    pos_x = (idx % 7) * ui.mainwin_wfactor + 1
    base_y = pos_y + 1
    arrow_x = pos_x + ui.mainwin_wfactor - 2

    cell_w = ui.mainwin_wfactor - 1
    cell_h = ui.mainwin_hfactor - 1

    # clear cell area
    for r in range(cell_h):
        try:
            ui.mainwin.addstr(pos_y + r, pos_x, " " * cell_w)
        except curses.error:
            pass

    # day numbers
    attr = 0
    # dim day numbers outside selected month
    if month != editor.selected_date.month:
        attr |= curses.color_pair(Colors.DIM)
    else:
        if (year, month, day) == (today.year, today.month, today.day):
            attr |= curses.color_pair(Colors.TODAY)
        if (year, month, day) == (selected.year, selected.month, selected.day):
            attr |= curses.A_REVERSE # selected date

    try:
        ui.mainwin.attron(attr)
        ui.mainwin.addstr(pos_y, pos_x, f"{day:>{cell_w}}")
        ui.mainwin.attroff(attr)
    except curses.error:
        pass

    # tasks
    max_per_day = ui.mainwin_hfactor - 2
    tasks = []
    for cal in editor.subcalendars:
        if cal.hidden:
            continue
        for t in cal.tasks:
            if (t.year, t.month, t.day) == (year, month, day):
                tasks.append((cal, t))

    scroll_offset = editor.task_scroll_offset if (year, month, day) == (selected.year, selected.month, selected.day) else 0
    visible = tasks[scroll_offset:scroll_offset + max_per_day]
    selected_index = editor.selected_task_index if (year, month, day) == (selected.year, selected.month, selected.day) else -1

    for i, (cal, t) in enumerate(visible):
        y = base_y + i
        attr = curses.color_pair(cal.color)
        text = f"{'✓ ' if t.completed else ''}{t.name[:cell_w - (2 if t.completed else 0)]}"
        if (year, month, day) == (selected.year, selected.month, selected.day) and (scroll_offset + i) == selected_index:
            attr |= curses.A_REVERSE

        try:
            ui.mainwin.attron(attr)
            ui.mainwin.addstr(y, pos_x, text)
            ui.mainwin.attroff(attr)
        except curses.error:
            pass

    # scroll indicators
    try:
        if scroll_offset > 0:
            ui.mainwin.addstr(base_y, arrow_x, "▲")
        if scroll_offset + max_per_day < len(tasks):
            ui.mainwin.addstr(base_y + len(visible) - 1, arrow_x, "▼")
    except curses.error:
        pass


# draw a full 6x7 calendar grid of day cells, starting from the last sunday before the 1st of the month
def _draw_full_grid(ui, editor):
    _draw_calendar_base(ui, editor)
    year, month = editor.selected_date.year, editor.selected_date.month
    first_of_month = date(year, month, 1)

    # last sunday before the first day of the month
    offset = (first_of_month.weekday() + 1) % 7  # Mon=0 Sun=6
    start_date = first_of_month - timedelta(days=offset)
    editor.first_visible_date = start_date

    # draw 42 days (6 weeks)
    for i in range(42):
        d = start_date + timedelta(days=i)
        _draw_day_cell(ui, editor, d.year, d.month, d.day)


def draw_screen(ui, editor):
    if editor.redraw or ui.redraw:
        # full redraw happens on significant events that warrant it (month changed, task addition/deletion, calendar visibility, term resize, etc)
        _draw_full_grid(ui, editor)
        editor.redraw_counter += 1
        ui.stdscr.refresh()
        editor.last_selected_date = editor.selected_date # this line fixes a bug, # TODO pass selected date directly to draw_day_cell
    else:
        # otherwise, we only redraw only necessary day cells
        if editor.last_selected_date != editor.selected_date:
            # redraw the old day cell to remove highlight
            _draw_day_cell(ui, editor, editor.last_selected_date.year, editor.last_selected_date.month, editor.last_selected_date.day)

        _draw_day_cell(ui, editor, editor.selected_date.year, editor.selected_date.month, editor.selected_date.day)

    if editor.mode is Mode.PROMPT and editor.prompt:
        # draw active prompt (input-in-progress)
        update_promptwin(
            ui,
            editor.prompt["text"] + editor.prompt["value"]
        )
    else:
        # normal status line
        _draw_prompt_status(ui, editor)

    ui.mainwin.noutrefresh()
    ui.promptwin.noutrefresh()
    curses.doupdate()
    
    editor.redraw = False
    ui.redraw = False