# License: MIT

"""
Shared helpers for normal and ex commands.
"""

from datetime import date, datetime, timedelta

from vical.commands.cmdargs import Mode


class UtilCmds:
    def __init__(self, editor):
        self.editor = editor

    def change_mode(self, cmdargs, mode):
        if cmdargs.mode == mode:
            return

        # Enter visual mode
        if cmdargs.mode == Mode.VISUAL:
            self.editor.visual_anchor_date = self.editor.selected_date

        # Leave visual mode
        elif mode == Mode.NORMAL:
            if self.editor.mode == Mode.VISUAL:
                self.editor.last_visual_anchor_date = self.editor.visual_anchor_date
                self.editor.visual_anchor_date = None

        cmdargs.mode = mode
        self.editor.status.request_redraw()

    def reset_editor(self, cmdargs):
        self.change_mode(cmdargs, Mode.NORMAL)
        self.editor.status.request_redraw()

    def parse_date_string(self, date_str: str):
        fmt = self.editor.settings.date_format.lower()
        current = self.editor.selected_date

        try:
            # 8 digits: DDMMYYYY/MMDDYYYY
            if len(date_str) == 8:
                if fmt == "mdy":
                    month = int(date_str[:2])
                    day = int(date_str[2:4])
                else:  # dmy
                    day = int(date_str[:2])
                    month = int(date_str[2:4])
                year = int(date_str[4:8])

            # 6 digits: MMYYYY, day = 1
            elif len(date_str) == 6:
                month = int(date_str[:2])
                year = int(date_str[2:6])
                day = 1

            # 4 digits: DDMM/MMDD, year = current
            elif len(date_str) == 4:
                if fmt == "mdy":
                    month = int(date_str[:2])
                    day = int(date_str[2:4])
                else:  # dmy
                    day = int(date_str[:2])
                    month = int(date_str[2:4])
                year = current.year

            # 1–2 digits: day only, month/year = current
            elif len(date_str) in (1, 2):
                day = int(date_str)
                month = current.month
                year = current.year

            else:
                return None

            return date(year, month, day)

        except Exception:
            return None

    def motion_to_date_interval(self, motion, repeats):
        start_date = motion.start
        interval_days = motion.days
        return [start_date + timedelta(days=interval_days * i) for i in range(repeats)]

    def create_task_instance(self, name: str, date: date, subcal=None):
        return Task(uid=None, name=name, date=date, completed=False, subcal=subcal)

    def create_event_instance(self, name: str, start_date: date, end_date: date, subcal=None):
        return Event(uid=None, name=name, start_date=start_date, end_date=end_date, subcal=subcal)

    def create_subcal_instance(self, name: str):
        return Subcalendar(name=name)

    def delete_subcal(self, subcal):
        tx_remove_subcal(self.editor, subcal)

    def change_subcal_name(self, subcal, new_name):
        tx_set_subcal_attr(self.editor, subcal, "name", new_name)

    def change_subcal_color(self, subcal, new_color):
        tx_set_subcal_attr(self.editor, subcal, "color", new_color)