# commands.py - Editor commands.
# This file is part of vical.
# License: MIT (see LICENSE)

from datetime import date, timedelta

from vical.core.editor import Mode, View
from vical.core.subcalendar import Subcalendar, CalendarItem, Task, Event
from vical.storage.jsonstore import save_subcalendars
from vical.history.ops import OpSetAttr, OpInsertItem, OpRemoveItem, OpMoveItem
from vical.history.transaction import set_attr, insert_item, remove_item, move_item, transaction


# ---- EDITOR COMMANDS ----
def quit(editor):
    """:quit

    Quit the program, check for unsaved changes.
    """
    if editor.dirty:
        editor.set_msg("No write since last change. Type :q! to force quit", error=1)
    else:
        raise SystemExit


def quit_bang(editor):
    """:quit!

    Force quit the program, disregard unsaved changes.
    """
    raise SystemExit


def write(editor):
    """:write

    Save changes.
    """
    try:
        save_subcalendars(editor.subcalendars)
    except Exception as e:
        editor.set_msg(f"{e}", error=1)
    editor.mark_saved()
    editor.set_msg("Write successful")


def write_quit(editor):
    """:writequit

    Save changes and quit
    """
    write(editor)
    quit(editor)


def change_mode(self, mode=None):
        """:change_mode <mode>

        Change mode to "visual" (selection) or "normal" mode.
        """
        if mode is None:
            self.fm.notify('Syntax: change_mode <mode>', bad=True)
            return
        if mode == self.mode:  # pylint: disable=access-member-before-definition
            return
        if mode == 'visual':
            self._visual_pos_start = self.thisdir.pointer
            self._visual_move_cycles = 0
            self._previous_selection = set(self.thisdir.marked_items)
            self.mark_files(val=not self._visual_reverse, movedown=False)
        elif mode == 'normal':
            if self.mode == 'visual':  # pylint: disable=access-member-before-definition
                self._visual_pos_start = None
                self._visual_move_cycles = None
                self._previous_selection = None
        else:
            return
        self.mode = mode
        self.ui.status.request_redraw()


def undo(editor):
    """:undo
    
    
    """
    if not editor.undo_stack:
        editor.set_msg("Undo: Already at oldest change")
        return

    tx = editor.undo_stack.pop()
    tx.revert(editor)
    editor.redo_stack.append(tx)

    editor.redraw = True
    editor.set_msg(f"Undo [#{tx.id}]: {tx.label}")


def redo(editor):
    """:redo
    
    
    """
    if not editor.redo_stack:
        editor.set_msg("Undo: Already at latest change")
        return

    tx = editor.redo_stack.pop()
    tx.apply(editor)
    editor.undo_stack.append(tx)

    editor.redraw = True
    editor.set_msg(f"Redo [#{tx.id}]: {tx.label}")


def show_help(editor):
    """:help

    Show the help screen.
    """
    pass # TODO


def toggle_monthly_view(editor):
    """:monthly

    Toggle monthly view.
    """
    editor.view = View.MONTHLY
    editor.redraw = True


def toggle_weekly_view(editor):
    """:weekly

    Toggle weekly view.
    """
    editor.view = View.WEEKLY
    editor.redraw = True


# ---- CALENDAR ITEMS ----
def new_task(editor):
    """:newtask

    Create a new task on the currently selected date within the currently selected subcalendar.
    """
    selected_date = editor.selected_date

    def execute(name):
        if not name.strip():
            editor.set_msg("Task name cannot be blank", error=1)
            return

        new_task = Task(uid=None, name=name, tdate=selected_date, completed=False)
        subcal = editor.selected_subcal

        msg=f"Create task '{new_task.name}' in subcal '{subcal.name}'"
        try:
            with transaction(editor, label=msg):
                insert_item(editor, subcal, new_task)
        except Exception as e:
            editor.set_msg(f"New task: '{name}': {e}", error=1)
            return

        editor.set_msg(msg)
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
    def execute(name):
        if not name.strip():
            editor.set_msg("Event name cannot be blank", error=1)
            return

        if editor.visual_anchor_date: # visual selection: start and end date have a range
            start = min(editor.visual_anchor_date, editor.selected_date)
            end = max(editor.visual_anchor_date, editor.selected_date)
        else: # no visual selection: start and end dates are the same
            start = end = editor.selected_date

        subcal = editor.selected_subcal
        new_event = Event(uid=None, name=name, start_date=start, end_date=end)

        msg=f"Create event '{new_event.name}' in subcal '{subcal.name}'"
        try:
            with transaction(editor, label=msg):
                insert_item(editor, subcal, new_event)
        except Exception as e:
            editor.set_msg(f"New event: '{name}': {e}", error=1)
            return

        editor.set_msg(msg)
        editor.visual_anchor_date = None
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
    task = editor.selected_item
    if not task or not isinstance(task, Task):
        return

    completed = not task.completed # reverse
    action = "Complete" if completed else "Uncomplete"

    try:
        with transaction(editor, label=f"{action} '{task.name}'"):
            set_attr(editor, task, "completed", completed)
    except Exception as e:
        editor.set_msg(f"Failed to mark complete '{task.name}': {e}", error=1)
        return

    editor.redraw = True


def rename_item(editor):
    """:renameitem
    
    Rename the selected item.
    """
    item = editor.selected_item
    if not item:
        editor.set_msg("Rename: No item selected")
        return

    def execute(new_name):
        if not new_name.strip():
            editor.set_msg("Item name cannot be blank", error=1)
            return
        old_name = item.name

        msg=f"Rename '{old_name}' to '{new_name}'"
        try:
            with transaction(editor, label=msg):
                set_attr(editor, item, "name", new_name)
        except Exception as e:
            editor.set_msg(f"Failed to rename item '{item.name}': {e}", error=1)
            return

        editor.set_msg(msg)
        editor.redraw = True

    editor.prompt = {
        "label": "",
        "user_input": "",
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
        editor.set_msg("Delete: No item selected")
        return

    msg=f"Delete '{item.name}' from '{item.parent_subcal.name}'"
    try:
        with transaction(editor, label=msg):
            editor.registers.set(item) # store item in the register
            remove_item(editor, item)
    except Exception as e:
        editor.set_msg(f"Failed to delete item '{item.name}': {e}", error=1)
        return

    editor.set_msg(msg)
    editor.redraw = True
    editor.clamp_item_index()


def yank_item(editor):
    """:yank

    Yank the selected item into the register.
    """
    item = editor.selected_item
    if not item:
        editor.set_msg("Yank: No item selected")
        return
    editor.registers.set(item)


def _resolve_date_selection(editor, event: Event):
    """
    Helper function to determine start_date end_date tuple from selection,
    used for event pasting.
    """
    # visual selection: pasted event dates cover visual selection
    if editor.visual_anchor_date:
        start = min(editor.visual_anchor_date, editor.selected_date)
        end = max(editor.visual_anchor_date, editor.selected_date)
        return start, end

    # normal selection: preserve original duration
    start = editor.selected_date
    end = start + timedelta(days=event.duration - 1)
    return start, end


def _paste_item(editor, original_subcal=True):
    """
    Resolve a calendar item from a register payload
    and paste it into a target subcalendar.
    """
    payload = editor.registers.get(editor.selected_register)
    if not payload:
        editor.set_msg("Paste: register is empty")
        return

    # build item from payload
    item = CalendarItem.from_register(payload)
    if isinstance(item, Task):
        item.date = editor.selected_date # tasks are always pasted on the selected date
    elif isinstance(item, Event):
        item.start_date, item.end_date = _resolve_date_selection(editor, item) # resolve date selection for smart event paste

    # determine target subcalendar
    if original_subcal:
        uid = payload.data.get("original_subcal_uid")
        target_subcal = editor.subcalendar_map.get(uid)
    else:
        target_subcal = editor.selected_subcal

    if not target_subcal:
        editor.set_msg("Subcalendar does not exist", error=1)
        return

    msg=f"Paste '{item.name}' into '{target_subcal.name}'"
    try:
        with transaction(editor, label=msg):
            insert_item(editor, target_subcal, item)
    except Exception as e:
        editor.set_msg(f"Failed to paste '{item.name}': {e}", error=1)
        return

    editor.set_msg(msg)
    editor.mode = Mode.NORMAL
    editor.visual_anchor_date = None
    editor.redraw = True


def paste_item_original_subcal(editor):
    """:paste

    Paste a calendar item into its original subcalendar.
    """
    _paste_item(editor, original_subcal=True)


def paste_item_selected_subcal(editor):
    """:paste

    Paste a calendar item into the currently selected subcalendar.
    """
    _paste_item(editor, original_subcal=False)


# ---- SUBCALENDARS ----
def new_subcal(editor):
    """:newcal

    Create a new subcalendar.
    """
    subcalendars = editor.subcalendars

    def execute(name):
        if not name.strip():
            editor.set_msg("Subcalendar name cannot be blank", error=1)
            return

        new_subcal = Subcalendar(name)

        try:
            subcalendars.append(new_subcal)
        except Exception as e:
            editor.set_msg(f"Failed to create subcalendar '{name}': {e}", error=1)
            return

        editor.set_msg(f"Created new subcalendar: '{name}'")
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
        editor.set_msg("No subcalendar selected", error=1)
        return

    def execute(new_name):
        if not new_name.strip():
            editor.set_msg("Subcalendar name cannot be blank", error=1)
            return
        try:
            with transaction(editor, label="Rename subcal"):
                set_attr(editor, subcal, "name", new_name)
        except Exception as e:
            editor.set_msg(f"Failed to rename subcalendar '{new_name}': {e}", error=1)
            return
        editor.set_msg(f"Renamed subcalendar to '{new_name}'")
        editor.redraw = True

    editor.prompt = {
        "label": "Rename subcalendar: ",
        "user_input": subcal.new_name,
        "on_submit": execute,
    }
    editor.mode = Mode.PROMPT


def delete_subcal(editor):
    """:delcal

    Delete the selected subcalendar
    """
    subcal = editor.selected_subcal
    if not subcal:
        editor.set_msg("No subcalendar selected", error=1)
        return

    def confirm_delete(resp):
        if resp.lower() != "y":
            editor.set_msg("Delete canceled")
            return
        try:
            with transaction(editor): # TODO
                editor.subcalendars.remove(subcal)
        except Exception as e:
            editor.set_msg(f"Failed to delete subcalendar '{subcal.name}': {e}", error=1)
            return
        editor.set_msg(f"Deleted subcalendar '{subcal.name}'")
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
    editor.set_msg(f"{subcal.name} {'hidden' if subcal.hidden else 'unhidden'}")
    editor.redraw = True


def change_subcal_color(editor):
    """:color

    Change the selected subcalendar color.
    """
    subcal = editor.selected_subcal

    if not subcal:
        editor.set_msg("No subcalendar selected", error=1)
        return

    def execute(new_color):
        if not new_color.strip():
            editor.set_msg(f"Color pair {new_color} does not exist", error=1)
            return
        try:
            with transaction(editor):
                set_attr(editor, subcal, "color", new_color)
        except Exception as e:
            editor.set_msg(f"Failed to change subcalendar color: {e}", error=1)
            return
        editor.set_msg(f"Changed subcalendar '{subcal.name}' color to '{subcal.color}'")
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
