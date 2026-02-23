# License: MIT

"""
Operator commands.
"""

from dataclasses import dataclass

from vical.core.subcalendar import Task
from vical.core.transaction import transaction_block, tx_set_item_attr, tx_remove_item

@dataclass
class OpArgs:
    op_key: str
    target_items: list
    regname: str = '"'
    text: str = ""


class Operators:
    def __init__(self, editor):
        self.editor = editor

    def do_operator(self, opargs: OpArgs):
        keymap = {
            'd': self.op_delete,
            'y': self.op_yank,
            'c': self.op_change,
            ' ': self.op_complete
        }
        fn = keymap.get(opargs.op_key.lower())
        if fn:
            fn(opargs)

    def op_delete(self, opargs: OpArgs):
        """
        Delete items and store them in the selected register.
        """
        if opargs.target_items:
            self.editor.registers.write(
                opargs.regname,
                opargs.target_items,
                rotate=True # Rotate numbered registers
            )
        with transaction_block(self.editor, label=f"Delete {len(opargs.target_items)} items"):
            for item in opargs.target_items:
                tx_remove_item(self.editor, item)

    def op_yank(self, opargs: OpArgs):
        """
        Yank items into the selected register.
        """
        if opargs.target_items:
            self.editor.registers.write(
                opargs.regname,
                opargs.target_items,
                rotate=False # Don't rotate numbered registers
            )

    def op_change(self, opargs: OpArgs):
        """
        Change the names of the items.
        """
        if not opargs.target_items or not opargs.text:
            return
        for item in opargs.target_items:
            tx_set_item_attr(self.editor, item, "name", opargs.text)

    def op_complete(self, opargs: OpArgs):
        """
        Toggle completion of all items that are tasks.
        """
        tasks = [t for t in opargs.target_items if ifinstance(t, Task)]
        if not tasks:
            return
        toggle = not all(t.completed for t in tasks)
        for t in tasks:
            tx_set_item_attr(self.editor, t, "completed", toggle)
