# commands.py - Editor commands.
# This file is part of vical.
# License: MIT (see LICENSE)

from datetime import date, timedelta

from vical.core.editor import Mode, View
from vical.core.subcalendar import Subcalendar, CalendarItem, Task, Event
from vical.core.state import capture_state, apply_state, compute_state_id, undoable
from vical.storage.jsonstore import save_subcalendars


# ---COMMON---
def quit(editor):
    """:quit

    Quit the program, check for unsaved changes.
    """
    if editor.modified:
        editor.msg = ("No write since last change. Type :q! to force quit", 1)
    else:
        raise SystemExit


def quit_bang(editor):
    """:quit!

    Force quit the program, disregarding unsaved changes.
    """
    raise SystemExit


def write(editor):
    """:write

    Save changes.
    """
    try:
        save_subcalendars(editor.subcalendars)
    except Exception as e:
        editor.msg = (f"{e}", 1)
    editor.mark_saved()
    editor.msg = ("Changes saved", 0)


def write_quit(editor):
    """:writequit

    Save changes and quit
    """
    write(editor)
    if not editor.modified:
        raise SystemExit


def undo(editor):
    """:undo

    Undo an action.
    """
    if not editor.undo_stack:
        editor.msg = ("Nothing to undo", 1)
        return
    # save current state for redo
    current = capture_state(editor)
    editor.redo_stack.append((current, compute_state_id(current)))
    # pop previous state and apply
    prev_state, _ = editor.undo_stack.pop()
    apply_state(editor, prev_state)
    # recompute change_id from the state we just applied
    editor.state_id = compute_state_id(prev_state)
    editor.msg = ("Undo", 0)


def redo(editor):
    """:redo

    Redo an action
    """
    if not editor.redo_stack:
        editor.msg = ("Nothing to redo", 1)
        return

    # save current state for undo
    current = capture_state(editor)
    editor.undo_stack.append((current, compute_state_id(current)))

    # pop redo state and apply
    redo_state, _ = editor.redo_stack.pop()
    apply_state(editor, redo_state)

    # recompute change_id from the state we just applied
    editor.change_id = compute_state_id(redo_state)

    editor.msg = ("Redo", 0)


def show_help(editor):
    """:help

    Show the help screen.
    """
    pass # TODO


# ---CALENDAR ITEMS---
def new_task(editor):
    """:newtask

    Create a new task on the currently selected date within the currently selected subcalendar.
    """
    selected_date = editor.selected_date

    def execute(name):
        if not name.strip():
            editor.msg = ("Task name cannot be blank", 1)
            return

        new_task = Task(uid=None, name=name, tdate=selected_date, completed=False)

        try:
            with undoable(editor):
                editor.selected_subcal.insert_item(new_task)
        except Exception as e:
            editor.msg = (f"New task: '{name}': {e}", 1)
            return

        editor.msg = (f"Created new task: '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Enter task name: ",
        "user_input": "",
        "on_submit": execute,
        "on_cancel": None,
    }
    editor.mode = Mode.PROMPT


def new_event(editor):
    """:newevent

    Create a new event on the currently selected date within the currently selected subcalendar.
    """
    selected_date = editor.selected_date

    def execute(name):
        if not name.strip():
            editor.msg = ("Event name cannot be blank", 1)
            return

        if not editor.visual_anchor_date: # no visual selection, single day date
            new_event = Event(uid=None, name=name, start_date=selected_date, end_date=selected_date)
        else: # visual selection supports date range
            _start_date = min(editor.visual_anchor_date, editor.selected_date)
            _end_date = max(editor.visual_anchor_date, editor.selected_date)
            new_event = Event(uid=None, name=name, start_date=_start_date, end_date=_end_date)

        try:
            with undoable(editor):
                editor.selected_subcal.insert_item(new_event)
        except Exception as e:
            editor.msg = (f"New event: '{name}': {e}", 1)
            return

        editor.msg = (f"Created new event: '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Enter event name: ",
        "user_input": "",
        "on_submit": execute,
        "on_cancel": None,
    }
    editor.mode = Mode.PROMPT


def mark_complete(editor):
    """:complete

    Mark the selected task completed.
    """
    item = editor.selected_item
    if not item:
        return  # nothing selected

    if not isinstance(item, Task):
        return # can only complete tasks

    try:
        with undoable(editor):
            item.toggle_completed()
    except Exception as e:
        editor.msg = (f"Failed to mark complete '{item.name}': {e}", 1)


def rename_item(editor):
    """:renameitem
    
    Rename the selected item.
    """
    item = editor.selected_item
    if not item:
        editor.msg = ("No item selected", 1)
        return

    def execute(name):
        if not name.strip():
            editor.msg = ("Item name cannot be blank", 1)
            return
        try:
            with undoable(editor):
                item.name = name
        except Exception as e:
            editor.msg = (f"Failed to rename item '{item.name}': {e}", 1)
            return
        editor.msg = (f"Renamed item to '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Rename item: ",
        "user_input": item.name,
        "on_submit": execute,
        "on_cancel": None,
    }
    editor.mode = Mode.PROMPT


def delete_item(editor):
    """:delitem

    Delete the currently selected item and store it in the register.
    """
    item = editor.selected_item
    if not item:
        editor.msg = ("No item selected", 1)
        return

    subcal = editor.selected_subcal

    try:
        with undoable(editor):
            removed = subcal.remove_item(item)
    except Exception as e:
        editor.msg = (f"Failed to delete item '{item.name}': {e}", 1)
        return

    # store deleted item in registers
    """
    entry = (removed.copy(), subcal)
    editor.registers['"'] = entry
    editor.registers['1'] = entry
    for i in range(9, 1, -1):
        editor.registers[str(i)] = editor.registers.get(str(i - 1))
    """

    editor.msg = (f"Deleted '{removed.name}'", 0)
    editor.redraw = True
    editor.clamp_item_index()


def yank_item(editor):
    """:yank

    Yank the selected item into the register.
    """
    item = editor.selected_item
    if not item:
        editor.msg = ("No item selected", 1)
        return

    entry = (item.copy(), editor.selected_subcal)
    editor.registers['"'] = entry
    editor.registers['0'] = entry
    editor.msg = (f"Yanked '{item.name}'", 0)


def paste_item(editor):
    """:paste

    Paste an item from the register into its original subcalendar.
    """
    reg = editor.registers['"']
    if not reg:
        editor.msg = ("Nothing to paste", 1)
        return

    item, original_subcal = reg
    new_item = item.copy()
    new_item.date = editor.selected_date

    target = original_subcal
    try:
        with undoable(editor):
            target.insert_item(new_item)
    except Exception as e:
        editor.msg = (f"Failed to paste item '{item.name}': {e}", 1)
        return

    editor.msg = (f"Pasted '{item.name}' into '{target.name}'", 0)
    editor.redraw = True


def paste_item_to_selected_subcal(editor):
    """:paste2

    Paste an item from the register into the currently selected subcalendar.
    """
    reg = editor.registers['"']
    if not reg:
        editor.msg = ("Nothing to paste", 1)
        return

    item, original_subcal = reg
    new_item = item.copy()
    new_item.date = editor.selected_date

    target = editor.selected_subcal
    try:
        with undoable(editor):
            target.insert_item(new_item)
    except Exception as e:
        editor.msg = (f"Failed to paste item '{item.name}': {e}", 1)
        return

    editor.msg = (f"Pasted '{item.name}' into '{target.name}'", 0)
    editor.redraw = True


# ---SUBCALENDARS---
def new_subcal(editor):
    """:newcal

    Create a new subcalendar.
    """
    subcalendars = editor.subcalendars

    def execute(name):
        if not name.strip():
            editor.msg = ("Subcalendar name cannot be blank", 1)
            return

        new_subcal = Subcalendar(name)

        try:
            with undoable(editor):
                subcalendars.append(new_subcal)
        except Exception as e:
            editor.msg = (f"Failed to create subcalendar '{name}': {e}", 1)
            return

        editor.msg = (f"Created new subcalendar: '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Enter subcalendar name: ",
        "user_input": "",
        "on_submit": execute,
        # "on_cancel": lambda: _cancel(editor),
    }
    editor.mode = Mode.PROMPT


def rename_subcal(editor):
    """:renamecal

    Rename the selected subcalendar.
    """
    subcal = editor.selected_subcal

    if not subcal:
        editor.msg = ("No subcalendar selected", 1)
        return

    def execute(name):
        if not name.strip():
            editor.msg = ("Subcalendar name cannot be blank", 1)
            return
        try:
            with undoable(editor):
                subcal.name = name
        except Exception as e:
            editor.msg = (f"Failed to rename subcalendar '{name}': {e}", 1)
            return
        editor.msg = (f"Renamed subcalendar to '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Rename subcalendar: ",
        "user_input": subcal.name,
        "on_submit": execute,
    }
    editor.mode = Mode.PROMPT


def delete_subcal(editor):
    """:delcal

    Delete the selected subcalendar
    """
    subcal = editor.selected_subcal
    if not subcal:
        editor.msg = ("No subcalendar selected", 1)
        return

    def confirm_delete(resp):
        if resp.lower() != "y":
            editor.msg = ("Delete canceled", 0)
            return
        try:
            with undoable(editor):
                editor.subcalendars.remove(subcal)
        except Exception as e:
            editor.msg = (f"Failed to delete subcalendar '{subcal.name}': {e}", 1)
            return
        editor.msg = (f"Deleted subcalendar '{subcal.name}'", 0)
        editor.redraw = True
        editor.selected_subcal_index = max(0, editor.selected_subcal_index - 1)

    editor.prompt = {
        "label": f"Delete subcalendar '{subcal.name}'? (y/N): ",
        "user_input": "",
        "on_submit": confirm_delete,
    }
    editor.mode = Mode.PROMPT


def hide_subcal(editor):
    """:hide

    Toggle visibility of the selected subcalendar.
    """
    subcal = editor.selected_subcal
    subcal.toggle_hidden()
    editor.msg = (f"{subcal.name} {'hidden' if subcal.hidden else 'unhidden'}", 0)
    editor.redraw = True


def change_subcal_color(editor):
    """:color

    Change the selected subcalendar color.
    """
    subcal = editor.selected_subcal

    if not subcal:
        editor.msg = ("No subcalendar selected", 1)
        return

    def execute(color):
        if not color.strip():
            editor.msg = ("No color", 1)
            return
        try:
            with undoable(editor):
                subcal.color = color
        except Exception as e:
            editor.msg = (f"Failed to change subcalendar color: {e}", 1)
            return
        editor.msg = (f"Changed subcalendar '{subcal.name}' color to '{subcal.color}'", 0)
        editor.redraw = True

    editor.prompt = {
        "label": "Change subcalendar color: ",
        "user_input": "",
        "on_submit": execute,
    }
    editor.mode = Mode.PROMPT


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


# ---OTHER---
def toggle_monthly_view(editor):
    editor.view = View.MONTHLY
    editor.redraw = True


def toggle_weekly_view(editor):
    editor.view = View.WEEKLY
    editor.redraw = True