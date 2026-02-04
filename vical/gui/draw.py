# draw.py - Calendar and prompt line drawing functions for Curses UI instance.
# This file is part of vical.
# License: MIT (see LICENSE)

import curses
import calendar
from datetime import date, timedelta

from vical.core.subcalendar import Task, Event
from vical.core.editor import Mode, View


def _attron(win, theme, color):
    win.attron(curses.color_pair(theme.pair(color)))


def _attroff(win, theme, color):
    win.attroff(curses.color_pair(theme.pair(color)))


def _get_day_name(day, editor):
    first_weekday = _get_first_weekday(editor)
    return calendar.day_abbr[(first_weekday + day) % 7]


def _get_month_name(month):
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    raise ValueError(f"Invalid month number: {month}")


def _get_first_weekday(editor) -> int:
    """
    Return the weekday index that the calendar starts on.
    6 = Sunday, 5 = Saturday
    """
    return editor.week_start


def _get_start_of_week(d: date, editor) -> date:
    """
    Given a date, return the date of the first day of that week
    according to editor.week_start.
    """
    first_weekday = _get_first_weekday(editor)
    delta = (d.weekday() - first_weekday) % 7
    return d - timedelta(days=delta)


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
        f"  {editor.last_motion}"
        f"{f' {editor.saved_state._id[:4]} {editor.active_state._id[:4]}' if editor.debug else ''}"
        f"{f'  {editor.redraw} {editor.redraw_counter}' if editor.debug else ''}"
        f"  {'[H]' if editor.selected_subcal.hidden else ''}"
    )

    subcal_name = editor.selected_subcal.name
    ui.promptwin.erase()

    try:
        # display selected item if any
        # if editor.selected_item:
        #     ui.promptwin.addstr(0, 0, editor.selected_item.name)

        # else:
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

    # grid lines 
    if editor.view == View.MONTHLY:
        # 6x7 rows/columns
        for y in range(1, 6):
            ui.mainwin.hline(ui.mainwin_hfactor * y, 0, curses.ACS_HLINE, ui.mainwin_w)
        for x in range(1, 7):
            ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    elif editor.view == View.WEEKLY:
        for x in range(1, 7):
            ui.mainwin.vline(0, ui.mainwin_wfactor * x, curses.ACS_VLINE, ui.mainwin_h)
    ui.mainwin.box()

    # day name headers
    for x in range(7):
        ui.mainwin.addstr(
            0,
            x * ui.mainwin_wfactor + CELL_TEXT_PADDING_X,
            _get_day_name(x, editor)[:ui.mainwin_wfactor - CELL_TEXT_PADDING_X]
        )

    # month footer with month name and year
    footer_str = f"{_get_month_name(editor.selected_date.month)}-{editor.selected_date.year}"
    footer_x = max(0, ui.mainwin_w - FOOTER_RIGHT_PADDING - len(footer_str))
    try:
        ui.mainwin.addstr(ui.mainwin_h - FOOTER_LEFT_PADDING, footer_x, footer_str)
    except curses.error:
        pass


def _get_selection_range(editor):
    """
    Return (start, end) of the currently selected date range.
    - Normal mode: start == end == selected_date
    - Visual mode: anchor and selected_date define the range
    """
    if editor.mode == Mode.VISUAL and editor.visual_anchor_date is not None:
        start = min(editor.visual_anchor_date, editor.selected_date)
        end = max(editor.visual_anchor_date, editor.selected_date)
    else:
        start = end = editor.selected_date
    return start, end


# layout constants for drawing day cells:
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


def _is_event_text_visible(editor, cell_date, item):
    return (
        cell_date == editor.selected_date or
        cell_date == item.start_date or
        cell_date.weekday() == editor.week_start
    )


# def _draw_day_cell_monthly(ui, editor, cell_date, theme): today = date.today() selected_date = editor.selected_date editor.max_items_visible = ui.mainwin_hfactor - (DAY_HEADER_ROWS + CELL_BORDER_THICKNESS) idx = (cell_date - editor.first_visible_date).days pos_y = (idx // 7) * ui.mainwin_hfactor + CELL_INSET_Y pos_x = (idx % 7) * ui.mainwin_wfactor + CELL_INSET_X base_y = pos_y + DAY_HEADER_ROWS arrow_x = pos_x + ui.mainwin_wfactor - CELL_RIGHT_PADDING cell_w = ui.mainwin_wfactor - CELL_BORDER_THICKNESS cell_h = ui.mainwin_hfactor - CELL_BORDER_THICKNESS # clear cell for r in range(cell_h): try: ui.mainwin.addstr(pos_y + r, pos_x, " " * cell_w) except curses.error: pass # day number attr = 0 if cell_date.month != selected_date.month: attr |= curses.color_pair(theme.pair("dim")) if cell_date == today: attr |= curses.color_pair(theme.pair("today")) start, end = _get_selection_range(editor) if start <= cell_date <= end: attr = curses.A_REVERSE try: ui.mainwin.attron(attr) ui.mainwin.addstr(pos_y, pos_x, f"{cell_date.day:>{cell_w}}") ui.mainwin.attroff(attr) except curses.error: pass # collect items items = [] for cal in editor.subcalendars: if cal.hidden: continue for item in cal.items: if item.occurs_on(cell_date): items.append((cal, item)) scroll_offset = editor.item_scroll_offset if cell_date == selected_date else 0 visible = items[scroll_offset:scroll_offset + editor.max_items_visible] selected_index = editor.selected_item_index if cell_date == selected_date else -1 def item_is_selected(i): return (scroll_offset + i) == selected_index # draw items for i, (cal, item) in enumerate(visible): y = base_y + i # ---------------- EVENTS ---------------- if isinstance(item, Event): base_attr = curses.color_pair(theme.pair(cal.color)) | curses.A_REVERSE is_selected = (cell_date == selected_date and item_is_selected(i)) text_x = pos_x + (len(SELECTION_MARKER) if is_selected else 0) text_w = cell_w - (text_x - pos_x) # background ribbon (ALWAYS full width) try: ui.mainwin.attron(base_attr) ui.mainwin.addstr(y, pos_x, " " * cell_w) ui.mainwin.attroff(base_attr) except curses.error: pass # ribbon text if _is_event_text_visible(editor, cell_date, item): if cell_date == item.start_date or is_selected: text = EVENT_RIBBON_START + " " + item.name else: text = " " + item.name try: ui.mainwin.attron(base_attr) ui.mainwin.addstr(y, text_x, text[:text_w]) ui.mainwin.attroff(base_attr) except curses.error: pass # ribbon end cap (NO reverse, true cell edge) if cell_date == item.end_date: end_attr = curses.color_pair(theme.pair(cal.color)) end_x = pos_x + cell_w - len(EVENT_RIBBON_END) try: ui.mainwin.attron(end_attr) ui.mainwin.addstr(y, end_x, EVENT_RIBBON_END) ui.mainwin.attroff(end_attr) except curses.error: pass # selection marker OVERLAY (last) if is_selected: try: ui.mainwin.addstr(y, pos_x, SELECTION_MARKER) except curses.error: pass continue # ---------------- TASKS ---------------- attr = curses.color_pair(theme.pair(cal.color)) if item.completed and editor.dim_when_completed: attr = curses.color_pair(theme.pair("dim")) text = f"{EVENT_COMPLETED_MARKER if item.completed else EVENT_UNCOMPLETED_MARKER}{item.name}" draw_x = pos_x if cell_date == selected_date and item_is_selected(i): try: ui.mainwin.addstr(y, pos_x, SELECTION_MARKER) except curses.error: pass draw_x += len(SELECTION_MARKER) try: ui.mainwin.attron(attr) ui.mainwin.addstr(y, draw_x, text[:cell_w - (draw_x - pos_x)]) ui.mainwin.attroff(attr) except curses.error: pass # scroll indicators try: if scroll_offset > 0: ui.mainwin.addstr(base_y, arrow_x, SCROLL_INDICATOR_UP) if scroll_offset + editor.max_items_visible < len(items): ui.mainwin.addstr( base_y + len(visible) - CELL_BORDER_THICKNESS, arrow_x, SCROLL_INDICATOR_DOWN ) except curses.error: pass


def _draw_day_cell_monthly(ui, editor, cell_date, theme):
    today = date.today()
    selected_date = editor.selected_date

    idx = (cell_date - editor.first_visible_date).days
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
    start, end = _get_selection_range(editor)
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
    for cal in editor.subcalendars:
        if cal.hidden:
            continue
        for item in cal.items:
            if item.occurs_on(cell_date):
                items.append((cal, item))

    max_items_visible = cell_h - DAY_HEADER_ROWS
    selected_index = editor.selected_item_index if cell_date == selected_date else -1
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
            if _is_event_text_visible(editor, cell_date, item):
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


def _draw_day_cell_weekly(ui, editor, cell_date, theme):
    today = date.today()
    selected_date = editor.selected_date

    cell_w = ui.mainwin_wfactor - CELL_BORDER_THICKNESS
    cell_h = ui.mainwin_h - ui.CAL_BORDERS

    day_index = (cell_date - editor.first_visible_date).days
    pos_x = day_index * ui.mainwin_wfactor + CELL_INSET_X
    pos_y = CELL_INSET_Y
    base_y = pos_y + DAY_HEADER_ROWS
    arrow_x = pos_x + ui.mainwin_wfactor - CELL_RIGHT_PADDING

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

    start, end = _get_selection_range(editor)
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
    for cal in editor.subcalendars:
        if cal.hidden:
            continue
        for item in cal.items:
            if item.occurs_on(cell_date):
                items.append((cal, item))

    max_items_visible = cell_h - DAY_HEADER_ROWS - CELL_BORDER_THICKNESS
    selected_index = editor.selected_item_index if cell_date == selected_date else -1
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

            # full-width background ribbon
            try:
                ui.mainwin.attron(base_attr)
                ui.mainwin.addstr(y, pos_x, " " * cell_w)
                ui.mainwin.attroff(base_attr)
            except curses.error:
                pass

            # ribbon text
            if _is_event_text_visible(editor, cell_date, item):
                if cell_date == item.start_date or is_selected:
                    text = EVENT_RIBBON_START + " " + item.name
                else:
                    text = " " + item.name
                try:
                    ui.mainwin.attron(base_attr)
                    ui.mainwin.addstr(y, text_x, text[:text_w])
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

            # selection marker overlay
            if is_selected:
                try:
                    ui.mainwin.addstr(y, pos_x, SELECTION_MARKER)
                except curses.error:
                    pass

            continue

        # ---- TASKS ----
        attr = curses.color_pair(theme.pair(cal.color))
        if getattr(item, "completed", False) and editor.dim_when_completed:
            attr = curses.color_pair(theme.pair("dim"))

        text = f"{EVENT_COMPLETED_MARKER if getattr(item, 'completed', False) else EVENT_UNCOMPLETED_MARKER}{item.name}"

        draw_x = pos_x
        if cell_date == selected_date and item_is_selected(i):
            try:
                ui.mainwin.addstr(y, pos_x, SELECTION_MARKER)
            except curses.error:
                pass
            draw_x += len(SELECTION_MARKER)

        try:
            ui.mainwin.attron(attr)
            ui.mainwin.addstr(y, draw_x, text[:cell_w - (draw_x - pos_x)])
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


def _draw_day_cell(ui, editor, cell_date, theme):
    if editor.view == View.MONTHLY:
        _draw_day_cell_monthly(ui, editor, cell_date, theme)
    if editor.view == View.WEEKLY:
        _draw_day_cell_weekly(ui, editor, cell_date, theme)


def _draw_full_month(ui, editor, theme):
    """
    Draw a full 6x7 grid of day cells to represent a full monthly calendar.
    """
    _draw_calendar_base(ui, editor)
    first_of_month = editor.selected_date.replace(day=1)

    # last sunday before the first day of the month
    start_date = _get_start_of_week(first_of_month, editor)
    editor.first_visible_date = start_date

    # draw 42 days (6 weeks)
    for i in range(42):
        d = start_date + timedelta(days=i)
        _draw_day_cell_monthly(ui, editor, d, theme)


def _draw_full_week(ui, editor, theme):
    """
    Draw a full row of 7 day cells to represent a full weekly schedule.
    """
    _draw_calendar_base(ui, editor)

    start_of_week = _get_start_of_week(editor.selected_date, editor)
    editor.first_visible_date = start_of_week

    for i in range(7):
        cell_date = start_of_week + timedelta(days=i)
        _draw_day_cell_weekly(ui, editor, cell_date, theme)


def draw_screen(ui, editor, theme):
    """
    Render the entire screen.
    """
    if editor.redraw:
        if editor.view == View.MONTHLY:
            _draw_full_month(ui, editor, theme)
        elif editor.view == View.WEEKLY:
            _draw_full_week(ui, editor, theme)

        editor.redraw_counter += 1
        ui.stdscr.refresh()
        editor.last_selected_date = editor.selected_date
    else:
        # redraw only changed day cells
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


def draw_screen_old(ui, editor, theme):
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
