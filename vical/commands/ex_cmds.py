# License: MIT

"""
Ex commands.
"""

from vical.storage.jsonstore import save_subcalendars_local_json


class ExCmds:
    def __init__(self, editor, utils):
        self.editor = editor
        self.utils = utils

    def ex_quit(self, cmdargs):
        if self.editor.dirty:
            return False
        raise SystemExit

    def ex_quit_bang(self, cmdargs):
        raise SystemExit

    def ex_write(self, cmdargs):
        save_subcalendars_local_json(self.editor.subcalendars)
        self.editor.mark_saved()
        return True

    def ex_write_quit(self, cmdargs):
        self.ex_write(cmdargs)
        self.ex_quit(cmdargs)

    def ex_set(self, cmdargs):
        pass

    def ex_let(self, cmdargs):
        pass
    
    def ex_task(self, cmdargs):
        """
        Creating new tasks with arguments.
        """
        pass

    def ex_event(self, cmdargs):
        """
        Creating new events with arguments.
        """
        pass

    def ex_put(self, cmdargs):
        pass # TODO

    def ex_new_subcal(self):
        pass # TODO

    def ex_delete_subcal(self, cmdargs):
        # this should take an argument to delete a subcal by name or default to editor.selected_subcal
        pass # TODO