# vical/ui/ui_actions.py
import curses
from datetime import date, timedelta
from ..subcalendar import Subcalendar, save_subcalendars, Task
from .ui_draw import update_prompt, draw_help, draw_screen

def _confirm(ui, text):
    update_prompt(ui, text)
    key = ui.promptwin.getch()
    return chr(key).lower() == 'y'


def write(ui):
    try:
        save_subcalendars(ui.subcalendars)
        ui.last_saved_snapshot = ui.snapshot_state()
        ui.saved = True
        ui.msg = ("Changes saved", 0)
    except Exception as e:
        ui.msg = (f"{e}", 1)


def quit(ui):
    if not ui.saved:
        ui.msg = ("No write since last change. Type :q! to force quit", 1)
    else:
        ui.running = False


def write_quit(ui):
    write(ui)
    if ui.saved:
        ui.running = False


def force_quit(ui):
    ui.running = False


def undo(ui):
    if not ui.history_undo:
        ui.msg = ("Nothing to undo", 1)
        return

    ui.history_redo.append(ui.snapshot_state())  # save current for redo
    snapshot = ui.history_undo.pop()
    ui.restore_state(snapshot)
    ui.msg = ("Undo", 0)


def redo(ui):
    if not ui.history_redo:
        ui.msg = ("Nothing to redo", 1)
        return

    ui.history_undo.append(ui.snapshot_state())  # save current before redoing
    snapshot = ui.history_redo.pop()
    ui.restore_state(snapshot)
    ui.msg = ("Redo", 0)


def show_help(ui):
    draw_help(ui)
    ui.stdscr.getch()
    ui.redraw = True
    draw_screen(ui)


# movement
def move(ui, motion):
    count = int(ui.count_buffer) if ui.count_buffer else 1
    new_date = ui.selected_date + timedelta(days=motion * count)

    try:
        ui.change_date(new_date, motion * count)
    except Exception as e:
        ui.msg = (f"{e}", 1)


def goto(ui):
    date_str = ui.count_buffer # use count_buffer as date string

    try:
        if(date_str):
            if len(date_str) == 8: # 8 digits: goto to MMDDYYYY
                month = int(date_str[:2])
                day = int(date_str[2:4])
                year = int(date_str[4:])
            elif len(date_str) == 6: # 6 digits: goto to MMYYYY
                month = int(date_str[:2])
                day = 1
                year = int(date_str[2:6])
            elif len(date_str) == 4: # 4 digits: goto to MMDD
                month = int(date_str[:2])
                day = int(date_str[2:4])
                year = ui.selected_date.year
            elif len(date_str) in (1, 2): # 1 or 2 digits: goto to M or MM
                month = int(date_str)
                day = 1
                year = ui.selected_date.year
            new_date = date(year, month, day)
            ui.msg = (f"goto: {new_date:%b %d, %Y}", 0)
        else:
            new_date = date.today() # jump to today if date string is empty
            ui.msg = ("goto: today", 0)

        ui.change_date(new_date)

    except Exception as e:
        ui.count_buffer = ''
        ui.msg = (f"{e}", 1)


# tasks
def new_task(ui):
    selected_date = ui.selected_date

    curses.curs_set(1)
    update_prompt(ui, "New task: ")
    curses.echo()
    try:
        name = ui.promptwin.getstr(0, 10, 50).decode('utf-8').strip() # TODO we should be able to escape this
    finally:
        curses.noecho()
        curses.curs_set(0)

    if not name or name == '':
        ui.msg = ("Task name cannot be blank", 1)
        return

    ui.selected_subcal.insert_task(Task(name, selected_date, 0))
    ui.msg = (f"Created new task: '{name}'", 0)
    ui.saved = False
    ui.redraw = True

    ui.push_history()

# TODO: these only work when the parent subcalendar is selected. these actions should be agnostic of the selected subcalendar
def yank_task(ui):
    task = ui.selected_task
    if not task:
        ui.msg = ("No task selected", 1)
        return

    # store both task and original subcal
    entry = (task.copy(), ui.selected_subcal)
    ui.registers['"'] = entry     # unnamed register
    ui.registers['0'] = entry     # last yank
    ui.msg = (f"Yanked '{task.name}'", 0)


def delete_task(ui):
    task = ui.selected_task
    if not task:
        ui.msg = ("No task selected", 1)
        return
    
    ui.push_history()

    subcal = ui.selected_subcal
    removed = subcal.pop_task(task)
    if not removed:
        ui.msg = ("Failed to delete task", 1)
        return

    # store deleted task
    entry = (removed.copy(), subcal)
    ui.registers['"'] = entry     # unnamed register
    ui.registers['1'] = entry     # last delete
    # shift older deletes
    for i in range(9, 1, -1):
        ui.registers[str(i)] = ui.registers.get(str(i - 1))

    ui.msg = (f"Deleted '{removed.name}'", 0)
    ui.saved = False
    ui.redraw = True
    ui.clamp_task_index()

def paste_task(ui):
    reg = ui.registers['"']
    if not reg:
        ui.msg = ("Nothing to paste", 1)
        return

    ui.push_history()

    task, original_subcal = reg
    new_task = task.copy()
    new_task.date = ui.selected_date

    target = original_subcal

    target.insert_task(new_task)
    ui.msg = (f"Pasted '{task.name}' into '{target.name}'", 0)
    ui.saved = False
    ui.redraw = True
    


def paste_task_to_selected_subcal(ui):
    reg = ui.registers['"']
    if not reg:
        ui.msg = ("Nothing to paste", 1)
        return

    ui.push_history()

    task, original_subcal = reg
    new_task = task.copy()
    new_task.date = ui.selected_date

    target = ui.selected_subcal

    target.insert_task(new_task)
    ui.msg = (f"Pasted '{task.name}' into '{target.name}'", 0)
    ui.saved = False
    ui.redraw = True


def rename_task(ui):
    task = ui.selected_task
    ui.push_history()


def mark_complete(ui):
    if ui.selected_task:
        ui.push_history()
        ui.selected_task.toggle_completed()
        ui.saved = False


def scroll_down(ui):
    tasks = ui.get_tasks_for_selected_day()
    if not tasks:
        return
    max_visible = ui.mainwin_hfactor - 2
    ui.selected_task_index = min(ui.selected_task_index + 1, len(tasks) - 1)
    if ui.selected_task_index >= ui.task_scroll_offset + max_visible:
        ui.task_scroll_offset += 1


def scroll_up(ui):
    tasks = ui.get_tasks_for_selected_day()
    if not tasks:
        return
    ui.selected_task_index = max(ui.selected_task_index - 1, 0)
    if ui.selected_task_index < ui.task_scroll_offset:
        ui.task_scroll_offset = ui.selected_task_index


# subcalendars
def new_subcal(ui):
    update_prompt(ui, "New subcalendar name: ")
    curses.echo()
    name = ui.promptwin.getstr(0, 22, 50).decode('utf-8').strip()
    curses.noecho()

    if not name:
        ui.msg = (f"Invalid name", 1)
        return

    ui.push_history()

    update_prompt(ui, "Choose color (1–5): ")
    for c in range(1, 6):
        ui.promptwin.attron(curses.color_pair(c))
        ui.promptwin.addstr(f"{c} ")
        ui.promptwin.attroff(curses.color_pair(c))
    ui.promptwin.refresh()

    while True:
        key = ui.promptwin.getch()
        if ord('1') <= key <= ord('5'):
            color = key - ord('0')
            break
        elif key == 27:
            ui.msg = ("Calendar creation canceled", 0)
            return

    new_cal = Subcalendar(name, color)
    ui.subcalendars.append(new_cal)
    ui.selected_subcal_index = len(ui.subcalendars) - 1
    ui.msg = (f"Created Subcalendar '{name}'", 0)
    ui.saved = False


def delete_subcal(ui):
    subcal = ui.selected_subcal
    if not subcal:
        ui.msg = ("No subcalendar selected", 1)
        return

    confirm = _confirm(ui, f"Delete subcalendar '{subcal.name}'? (y/N): ")
    if confirm:
        ui.msg = ("Cancelled", 0)
        return

    ui.push_history()

    try:
        ui.subcalendars.remove(subcal)
        ui.msg = (f"Deleted subcalendar '{subcal.name}'", 0)
        ui.saved = False
        ui.redraw = True

        # adjust index so it doesn't go out of range
        ui.selected_subcal_index = max(0, ui.selected_subcal_index - 1)

    except ValueError:
        ui.msg = (f"Failed to delete subcalendar '{subcal.name}'", 1)



def rename_subcal(ui):
    subcal = ui.selected_subcal
    # TODO


def hide_subcal(ui):
    subcal = ui.selected_subcal
    subcal.toggle_hidden()
    ui.msg = (f"{subcal.name} {'hidden' if subcal.hidden else 'unhidden'}", 0)
    ui.redraw = True


def cycle_subcal(ui, direction: int):
    if not ui.subcalendars:
        return
    ui.selected_subcal_index = (ui.selected_subcal_index + direction) % len(ui.subcalendars)


def next_subcal(ui):
    if not ui.subcalendars:
        return
    ui.selected_subcal_index = (ui.selected_subcal_index + 1) % len(ui.subcalendars)


def prev_subcal(ui):
    if not ui.subcalendars:
        return
    ui.selected_subcal_index = (ui.selected_subcal_index - 1) % len(ui.subcalendars)


def change_subcal_color(ui):
    subcal = ui.selected_subcal
    if not subcal:
        return

    ui.push_history()

    update_prompt(ui, f"Choose color for '{subcal.name}': ")
    for c in range(1, 6):
        ui.promptwin.attron(curses.color_pair(c))
        ui.promptwin.addstr(f"{c} ")
        ui.promptwin.attroff(curses.color_pair(c))
    ui.promptwin.refresh()

    while True:
        key = ui.promptwin.getch()
        if ord('1') <= key <= ord('5'):
            color = key - ord('0')
            subcal.change_color(color)
            ui.msg = (f"Color changed for {subcal.name}", 0)
            return
        elif key == 27:
            return