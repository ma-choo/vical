# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from datetime import date, timedelta


def move(editor, motion):
    """
    Move motion amount of days, use count as a multiplier
    """
    count = int(editor.count) if editor.count else 1
    new_date = editor.selected_date + timedelta(days=motion * count)

    try:
        editor.change_date(new_date, motion * count)
    except Exception as e:
        editor.msg = (f"{e}", 1)


def goto(editor):
    """
    Goto a specific date using count as a date destination,
    or jump back to the current date if count is empty.
    """
    date_str = editor.count
    editor.count = ''  # always clear buffer

    if not date_str: # jump to today
        new_date = date.today()
        editor.msg = ("goto: today", 0)
        editor.change_date(new_date)
        return

    try:
        if len(date_str) == 8: ## MMDDYYY
            month, day, year = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:])
        elif len(date_str) == 6: # MMYYYY, day = 1
            month, day, year = int(date_str[:2]), 1, int(date_str[2:6])
        elif len(date_str) == 4: # MMDD, year = current
            month, day, year = int(date_str[:2]), int(date_str[2:4]), editor.selected_date.year
        elif len(date_str) in (1, 2): # D/DD, month/year = current
            month, day, year = int(date_str), 1, editor.selected_date.year
        else:
            raise ValueError

        new_date = date(year, month, day)
        editor.msg = (f"goto: {new_date:%b %d, %Y}", 0)
        editor.change_date(new_date)

    except Exception as e:
        editor.msg = (f"Invalid date: {date_str}", 1)


def left(editor):
    move(editor, -1)


def right(editor):
    move(editor, 1)


def up(editor):
    move(editor, -7)


def down(editor):
    move(editor, 7)


def visual_down(editor):
    tasks = editor.get_tasks_for_selected_day()
    if not tasks:
        return

    max_visible = self.mainwin_hfactor - 2
    editor.selected_task_index = min(editor.selected_task_index + 1, len(tasks) - 1)
    if editor.selected_task_index >= editor.task_scroll_offset + max_visible:
        self.task_scroll_offset += 1


def visual_up(editor):
    tasks = editor.get_tasks_for_selected_day()
    if not tasks:
        return

    editor.selected_task_index = max(editor.selected_task_index - 1, 0)
    if editor.selected_task_index < self.task_scroll_offset:
        self.task_scroll_offset = editor.selected_task_index


def next_subcal(editor):
    """
    Cycle subcalendar selection forward.
    """
    if not editor.subcalendars:
        return
    editor.selected_subcal_index = (editor.selected_subcal_index + 1) % len(editor.subcalendars)


def prev_subcal(editor):
    """
    Cycle subcalendar selection backward.
    """
    if not editor.subcalendars:
        return
    editor.selected_subcal_index = (editor.selected_subcal_index - 1) % len(editor.subcalendars)
