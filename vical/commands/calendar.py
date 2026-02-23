# License: MIT

"""
Functions for working with subcalendars and calendar items
"""

from vical.commands.tx import tx_insert_item


class CalendarCmds:
    def __init__(self, editor, utils):
        self.editor = editor
        self.utils = utils

    def do_create_tasks(self, dates, name, subcal):
        """
        Create one task per date.
        """
        for d in dates:
            task = self.utils.create_task_instance(
                name=name,
                date=d,
                subcal=subcal,
            )
            tx_insert_item(self.editor, task, subcal)

    def do_create_single_day_events(self, dates, name, subcal):
        """
        Create one single-day event per date.
        """
        for d in dates:
            event = self.utils.create_event_instance(
                name=name,
                start_date=d,
                end_date=d,
                subcal=subcal,
            )
            tx_insert_item(self.editor, event, subcal)

    def do_create_spanning_event(self, start_date, end_date, name, subcal):
        """
        Create one multi-day event spanning a range.
        """
        event = self.utils.create_event_instance(
            name=name,
            start_date=start_date,
            end_date=end_date,
            subcal=subcal,
        )
        tx_insert_item(self.editor, event, subcal)

    def do_toggle_subcal_hidden(self, subcal=None):
        """
        Toggle visibility of a subcalendar.
        """
        self.editor.selected_subcal.toggle_hidden()
