# This file is part of vical.
# License: MIT (see LICENSE)

from datetime import date, timedelta
from vical.core.editor import Mode
from vical.core.subcalendar import Subcalendar, save_subcalendars, Task
from vical.core.state import capture_state, apply_state, compute_state_id, undoable


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


# ---TASKS---
def new_task(editor):
    """:newtask

    Create a new task.
    """
    selected_date = editor.selected_date

    def execute(name):
        if not name.strip():
            editor.msg = ("Task name cannot be blank", 1)
            return

        try:
            with undoable(editor):
                editor.selected_subcal.insert_task(Task(name, selected_date, 0))
        except Exception as e:
            editor.msg = (f"Failed to create task '{name}': {e}", 1)
            return

        editor.msg = (f"Created new task: '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "text": "Enter task name: ",
        "value": "",
        "on_submit": execute,
        "on_cancel": None,
    }
    editor.mode = Mode.PROMPT


def mark_complete(editor):
    """:complete

    Mark the selected task completed.
    """
    task = editor.selected_task
    if task:
        try:
            with undoable(editor):
                task.toggle_completed()
        except Exception as e:
            editor.msg = (f"Failed to mark complete '{task.name}': {e}", 1)


def rename_task(editor):
    """:renametask
    
    Rename the selected task.
    """
    task = editor.selected_task
    if not task:
        editor.msg = ("No task selected", 1)
        return

    def execute(name):
        if not name.strip():
            editor.msg = ("Task name cannot be blank", 1)
            return
        try:
            with undoable(editor):
                task.name = name
        except Exception as e:
            editor.msg = (f"Failed to rename task '{task.name}': {e}", 1)
            return
        editor.msg = (f"Renamed task to '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "text": "Rename task: ",
        "value": task.name,
        "on_submit": execute,
        "on_cancel": None,
    }
    editor.mode = Mode.PROMPT


def delete_task(editor):
    """:deltask

    Delete the currently selected task and store it in the register.
    """
    task = editor.selected_task
    if not task:
        editor.msg = ("No task selected", 1)
        return

    subcal = editor.selected_subcal

    try:
        with undoable(editor):
            removed = subcal.pop_task(task)
    except Exception as e:
        editor.msg = (f"Failed to delete task '{task.name}': {e}", 1)
        return

    # store deleted task in registers
    entry = (removed.copy(), subcal)
    editor.registers['"'] = entry     # unnamed register
    editor.registers['1'] = entry     # last delete
    # shift older deletes
    for i in range(9, 1, -1):
        editor.registers[str(i)] = editor.registers.get(str(i - 1))

    editor.msg = (f"Deleted '{removed.name}'", 0)
    editor.redraw = True
    editor.clamp_task_index()


def yank_task(editor):
    """:yank

    Yank the selected task into the register.
    """
    task = editor.selected_task
    if not task:
        editor.msg = ("No task selected", 1)
        return

    # store both task and original subcal
    entry = (task.copy(), editor.selected_subcal)
    editor.registers['"'] = entry # unnamed register
    editor.registers['0'] = entry # last yank
    editor.msg = (f"Yanked '{task.name}'", 0)


def paste_task(editor):
    """:paste

    Paste a task from the register into its original subcalendar.
    """
    reg = editor.registers['"']
    if not reg:
        editor.msg = ("Nothing to paste", 1)
        return

    task, original_subcal = reg
    new_task = task.copy()
    new_task.date = editor.selected_date

    target = original_subcal

    try:
        with undoable(editor):
            target.insert_task(new_task)
    except Exception as e:
        editor.msg = (f"Failed to paste task '{task.name}': {e}", 1)
        return

    editor.msg = (f"Pasted '{task.name}' into '{target.name}'", 0)
    editor.redraw = True
    

def paste_task_to_selected_subcal(editor):
    """:paste2

    Paste a task from the register into the currently selected subcalendar.
    """
    reg = editor.registers['"']
    if not reg:
        editor.msg = ("Nothing to paste", 1)
        return

    task, original_subcal = reg
    new_task = task.copy()
    new_task.date = editor.selected_date

    target = editor.selected_subcal

    try:
        with undoable(editor):
            target.insert_task(new_task)
    except Exception as e:
        editor.msg = (f"Failed to paste task '{task.name}': {e}", 1)
        return

    editor.msg = (f"Pasted '{task.name}' into '{target.name}'", 0)
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

        subcal = Subcalendar(name, 1)

        try:
            with undoable(editor):
                subcalendars.append(subcal)
        except Exception as e:
            editor.msg = (f"Failed to create subcalendar '{name}': {e}", 1)
            return

        editor.msg = (f"Created new subcalendar: '{name}'", 0)
        editor.redraw = True

    editor.prompt = {
        "text": "Enter subcalendar name: ",
        "value": "",
        "on_submit": execute,
        "on_cancel": lambda: _cancel(editor),
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
        "text": "Rename subcalendar: ",
        "value": subcal.name,
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
        "text": f"Delete subcalendar '{subcal.name}'? (y/N): ",
        "value": "",
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
        editor.msg = (f"Renamed subcalendar '{subcal.name}' color to '{subcal.color}'", 0)
        editor.redraw = True

    editor.prompt = {
        "text": "Change subcalendar color: ",
        "value": "",
        "on_submit": execute,
    }
    editor.mode = Mode.PROMPT