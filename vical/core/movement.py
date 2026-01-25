# movement.py - Editor navigation.
# This file is part of vical.
# License: MIT (see LICENSE)

import curses
from datetime import date, timedelta


def move(editor, motion):
    """
    Apply a relative date motion (days or weeks), respecting a numeric count.
    Computes the target date and delegates the actual date change to the editor.
    """
    count = int(editor.count) if editor.count else 1
    new_date = editor.selected_date + timedelta(days=motion * count)
    editor.change_date(new_date, motion * count)


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
    """
    Move the cursor selection one day backward.
    """
    move(editor, -1)


def right(editor):
    """
    Move the cursor selection one day foreward.
    """
    move(editor, 1)


def up(editor):
    """
    Move the cursor selection one week backward.
    """
    move(editor, -7)


def down(editor):
    """
    Move the cursor selection one week foreward.
    """
    move(editor, 7)

# TODO: these visual movements should support count
def visual_left(editor):
    """
    Visual move one day left without resetting task selection.
    """
    new_date = editor.selected_date - timedelta(days=1)
    editor.set_date(new_date, reset_tasks=False)
    editor.clamp_task_index()
    editor.ensure_task_visible()


def visual_right(editor):
    """
    Visual move one day right without resetting task selection.
    """
    new_date = editor.selected_date + timedelta(days=1)
    editor.set_date(new_date, reset_tasks=False)
    editor.clamp_task_index()
    editor.ensure_task_visible()


def visual_up(editor):
    """
    Visual move one task up.
    Goes up one task within the day cell,
    or if already at the top, jump one week back and select the last task of that day.
    """
    if editor.selected_task_index > 0:
        editor.selected_task_index -= 1
        editor.ensure_task_visible()
        return

    new_date = editor.selected_date - timedelta(days=7)
    editor.set_date(new_date, reset_tasks=True)

    # jump to bottom if tasks exist
    editor.selected_task_index = editor.max_task_index()
    editor.ensure_task_visible()

    
def visual_down(editor):
    """
    Visual move one task down.
    Goes down one task within the day cell,
    or if already at the top, jump one week back and select the last task of that day.
    """
    tasks = editor.get_tasks_for_selected_day()

    if editor.selected_task_index < len(tasks) - 1:
        editor.selected_task_index += 1
        editor.ensure_task_visible()
        return

    # cross week boundary
    new_date = editor.selected_date + timedelta(days=7)
    editor.set_date(new_date, reset_tasks=True)
