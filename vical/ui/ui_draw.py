# vical/ui/ui_draw.py
import curses
from datetime import date, timedelta
from ..utils import get_day_name, get_month_name

def update_prompt(ui, text):
    ui.promptwin.erase()
    ui.promptwin.addstr(0, 0, text)
    ui.promptwin.noutrefresh()
    curses.doupdate()


def draw_help(ui):
    curses.curs_set(0)
    ui.mainwin.erase()
    ui.mainwin.addstr(ui.HELP)
    ui.mainwin.noutrefresh()
    update_prompt(ui, "Help - press any key to continue")


def _draw_prompt_status(ui):
    msg, is_error = ui.msg
    curses.curs_set(0)

    status_prefix = (
        f"{'[+]' if not ui.saved else ''}"                 # unsaved marker
        f"{f'  {ui.operator} ' if ui.operator else ' '}"   # operator
        f"{f'  {ui.count_buffer}' if ui.count_buffer else ''}"           # count
        f"  {ui.last_motion}"                                   # motion
        f"{f'  {ui.redraw} {ui.redraw_counter}' if ui.debug else ''}"  # redraw counter
        f"  {'[H]' if ui.selected_subcal.hidden else ''}"  # hidden flag
    )

    subcal_name = ui.selected_subcal.name
    ui.promptwin.erase()

    try:
        # display selected task if any
        if ui.selected_task:
            ui.promptwin.addstr(0, 0, ui.selected_task.name)
        else:
            if is_error:
                ui.promptwin.attron(curses.color_pair(2))  # red
                ui.promptwin.addstr(0, 0, f"ERROR: {msg}")
                ui.promptwin.attroff(curses.color_pair(2))
            else:
                ui.promptwin.addstr(0, 0, msg)

        # draw the uncolored part of the status line
        right_x = ui.mainwin_w - (len(status_prefix) + len(subcal_name))
        ui.promptwin.addstr(0, right_x, status_prefix)

        # draw the subcalendar name in its color
        ui.promptwin.attron(curses.color_pair(ui.selected_subcal.color))
        ui.promptwin.addstr(0, right_x + len(status_prefix), subcal_name)
        ui.promptwin.attroff(curses.color_pair(ui.selected_subcal.color))

    except Exception as e:
        ui.promptwin.attron(curses.color_pair(2))
        ui.promptwin.addstr(0, 0, f"ERROR: {e}")
        ui.promptwin.attroff(curses.color_pair(2))



# draw static calendar elements (grid lines, day headers, month footer)
def _draw_calendar_base(ui):
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
                              get_day_name(x)[:ui.mainwin_wfactor - 1])
        except curses.error:
            pass

    # month footer
    footer_str = f"{get_month_name(ui.selected_date.month)}-{ui.selected_date.year}"
    footer_x = max(0, ui.mainwin_w - 2 - len(footer_str))
    try:
        ui.mainwin.addstr(ui.mainwin_h - 1, footer_x, footer_str)
    except curses.error:
        pass



# draw a single day cell (number, tasks, highlights)
def _draw_day_cell(ui, year, month, day):
    today = date.today()
    selected = ui.selected_date

    # calculate cell index relative to first visible date
    idx = (date(year, month, day) - ui.first_visible_date).days
    pos_y = (idx // 7) * ui.mainwin_hfactor + 1
    pos_x = (idx % 7) * ui.mainwin_wfactor + 1
    base_y = pos_y + 1
    arrow_x = pos_x + ui.mainwin_wfactor - 2

    cell_w = ui.mainwin_wfactor - 1
    cell_h = ui.mainwin_hfactor - 1

    # clear cell area safely
    for r in range(cell_h):
        try:
            ui.mainwin.addstr(pos_y + r, pos_x, " " * cell_w)
        except curses.error:
            pass

    # day numbers
    attr = 0
    # dim day numbers outside selected month
    if month != ui.selected_date.month:
        attr |= curses.color_pair(6)  # dim color
    else:
        if (year, month, day) == (today.year, today.month, today.day):
            attr |= curses.color_pair(7) # current date
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
    for cal in ui.subcalendars:
        if cal.hidden:
            continue
        for t in cal.tasks:
            if (t.year, t.month, t.day) == (year, month, day):
                tasks.append((cal, t))

    scroll_offset = ui.task_scroll_offset if (year, month, day) == (selected.year, selected.month, selected.day) else 0
    visible = tasks[scroll_offset:scroll_offset + max_per_day]
    selected_index = ui.selected_task_index if (year, month, day) == (selected.year, selected.month, selected.day) else -1

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
def _draw_full_grid(ui):
    _draw_calendar_base(ui)
    year, month = ui.selected_date.year, ui.selected_date.month
    first_of_month = date(year, month, 1)

    # last sunday before the first day of the month
    offset = (first_of_month.weekday() + 1) % 7  # Mon=0 Sun=6
    start_date = first_of_month - timedelta(days=offset)
    ui.first_visible_date = start_date

    # draw 42 days (6 weeks)
    for i in range(42):
        d = start_date + timedelta(days=i)
        _draw_day_cell(ui, d.year, d.month, d.day)


def draw_screen(ui):
    if ui.redraw:
        # full redraw happens on significant events that warrant it (month changed, task addition/deletion, calendar visibility, term resize, etc)
        _draw_full_grid(ui)
        ui.redraw_counter += 1
        ui.stdscr.refresh()
        ui.last_selected_date = ui.selected_date # this line fixes a bug, #TODO pass selected date directly to draw_day_cell
    else:
        # otherwise, we only redraw only necessary day cells
        if ui.last_selected_date != ui.selected_date:
            # redraw the old day cell to remove highlight
            _draw_day_cell(ui, ui.last_selected_date.year, ui.last_selected_date.month, ui.last_selected_date.day)

        _draw_day_cell(ui, ui.selected_date.year, ui.selected_date.month, ui.selected_date.day)

    _draw_prompt_status(ui)
    ui.mainwin.noutrefresh()
    ui.promptwin.noutrefresh()
    curses.doupdate()
    
    ui.redraw = False