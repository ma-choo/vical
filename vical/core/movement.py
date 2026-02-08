# movement.py - Editor navigation.
# This file is part of vical.
# License: MIT (see LICENSE)

from datetime import date, timedelta


def move(editor, motion, count=None):
    """
    Move the selection by motion * count days.
    - In VISUAL mode, extends or shrinks the selection tuple.
    - In NORMAL mode, resets selection.
    """
    count = int(count) if count is not None else int(editor.count or 1)
    delta = motion * count
    new_date = editor.selected_date + timedelta(days=delta)
    editor.set_selected_date(new_date, reset_items=True, record_motion=delta)


def goto(editor):
    """
    Goto a specific date using count as a date destination,
    or jump back to today if count is empty.
    """
    date_str = editor.count
    editor.count = ""  # always clear buffer

    if not date_str:
        new_date = date.today()
        editor.set_msg("Goto: Today")
        editor.set_selected_date(new_date, reset_items=True)
        return

    try:
        if len(date_str) == 8:  # MMDDYYYY
            month, day, year = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:])
        elif len(date_str) == 6:  # MMYYYY, day = 1
            month, day, year = int(date_str[:2]), 1, int(date_str[2:6])
        elif len(date_str) == 4:  # MMDD, year = current
            month, day, year = int(date_str[:2]), int(date_str[2:4]), editor.selected_date.year
        elif len(date_str) in (1, 2):  # D/DD, month/year = current
            month, day, year = int(date_str), 1, editor.selected_date.year
        else:
            raise ValueError

        new_date = date(year, month, day)
        editor.set_msg(f"Goto: {new_date:%b %d %Y}")
        editor.set_selected_date(new_date, reset_items=True)
    except Exception:
        editor.set_msg(f"Invalid date: {date_str}", error=1)


def left(editor, count=1):
    new_date = editor.selected_date - timedelta(days=count)
    editor.set_selected_date(new_date, reset_items=True, record_motion=-count)


def right(editor, count=1):
    new_date = editor.selected_date + timedelta(days=count)
    editor.set_selected_date(new_date, reset_items=True, record_motion=count)


def up(editor, count=1):
    new_date = editor.selected_date - timedelta(days=7 * count)
    editor.set_selected_date(new_date, reset_items=True, record_motion=-7 * count)


def down(editor, count=1):
    new_date = editor.selected_date + timedelta(days=7 * count)
    editor.set_selected_date(new_date, reset_items=True, record_motion=7 * count)


def visual_left(editor, count=1):
    new_date = editor.selected_date - timedelta(days=count)
    editor.set_selected_date(new_date, reset_items=False)
    editor.clamp_item_index()

def visual_right(editor, count=1):
    new_date = editor.selected_date + timedelta(days=count)
    editor.set_selected_date(new_date, reset_items=False)
    editor.clamp_item_index()

def visual_up(editor, count=1):
    """Move one item up in the current day, jump a week if at top."""
    for _ in range(count):
        if editor.selected_item_index > 0:
            editor.selected_item_index -= 1
            continue
        new_date = editor.selected_date - timedelta(days=7)
        editor.set_selected_date(new_date, reset_items=True)
        editor.selected_item_index = editor.max_item_index()


def visual_down(editor, count=1):
    """Move one item down in the current day, jump a week if at bottom."""
    for _ in range(count):
        items = editor.get_items_for_selected_day()
        if editor.selected_item_index < len(items) - 1:
            editor.selected_item_index += 1
            continue
        new_date = editor.selected_date + timedelta(days=7)
        editor.set_selected_date(new_date, reset_items=True)
        editor.selected_item_index = 0
