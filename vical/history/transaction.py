# transaction.py - Operations for history tracking
# This file is part of vical.
# License: MIT (see LICENSE)

"""
This module defines Transactions, which group multiple operations (ops) into a single
undoable action.
"""

from contextlib import contextmanager

from vical.history.ops import OpSetAttr, OpInsertItem, OpRemoveItem, OpMoveItem


class Transaction:
    """
    A Transaction is an ordered list of ops that should be applied or
    reverted as a single unit.

    Transactions are pushed onto the editor's undo stack.
    """
    _next_id = 1

    def __init__(self, label: str = ""):
        self.id = Transaction._next_id
        Transaction._next_id += 1
        self.ops: list[Op] = []
        self.label = label

    def apply(self, editor):
        """
        Apply all ops in forward order.
        """
        for op in self.ops:
            op.apply(editor)

    def revert(self, editor):
        """
        Revert all ops in reverse order.

        Reversing is critical to ensure state is restored correctly
        """
        for op in reversed(self.ops):
            op.revert(editor)


def begin_transaction(editor, label=""):
    """
    Begin a new transaction on the editor.

    Nested transactions are not allowed to keep undo/redo semantics simple.
    """
    if hasattr(editor, "_current_tx") and editor._current_tx is not None:
        raise RuntimeError("Nested transactions are not allowed")
    editor._current_tx = Transaction(label)


def record(editor, op: Op):
    """
    Record an Op in the currently active transaction.

    All mutating editor actions must go through record() so they are
    undoable.
    """
    if not hasattr(editor, "_current_tx") or editor._current_tx is None:
        raise RuntimeError("record() called outside of transaction")
    editor._current_tx.ops.append(op)


def commit_transaction(editor):
    """
    Commit the active transaction to the undo stack.

    Empty transactions are discarded
    Redo history is cleared on commit
    History length is capped
    """
    # do not record no-op transactions
    if not hasattr(editor, "_current_tx") or editor._current_tx is None:
        return
    if not editor._current_tx.ops:
        editor._current_tx = None
        return

    editor.undo_stack.append(editor._current_tx)
    editor.redo_stack.clear()

    # enforce maximum history length
    if len(editor.undo_stack) > editor.MAX_HISTORY:
        editor.undo_stack.pop(0)
    editor._current_tx = None


def set_attr(editor, item, attr, new):
    """
    Helper for setting an attribute with history tracking.

    Records an OpSetAttr before mutating the object.
    """
    old = getattr(item, attr)
    if old == new:
        return

    record(editor, OpSetAttr(item.uid, attr, old, new))
    setattr(item, attr, new)


def insert_item(editor, subcal, item):
    """
    Insert an item into a subcalendar with history tracking.

    Preconditions:
    - item is not currently attached to any subcalendar # TODO why?
    """
    assert item.parent_subcal is None, "Item already belongs to a subcalendar"

    # Record the insertion before mutating state
    record(editor, OpInsertItem(subcal.uid, item))

    # Apply mutation immediately
    item.parent_subcal = subcal
    subcal.items.append(item)
    subcal.items.sort(key=lambda i: i.sort_key())


def remove_item(editor, item):
    """
    Remove an item from its current subcalendar with history tracking.

    Preconditions:
    - item must belong to a subcalendar
    """
    subcal = item.parent_subcal
    assert subcal is not None, "Item does not belong to a subcalendar"

    record(editor, OpRemoveItem(subcal.uid, item))

    subcal.items.remove(item)
    item.parent_subcal = None
    subcal.items.sort(key=lambda i: i.sort_key())


def move_item(editor, item, dst_subcal):
    """
    Move an item from its parent subcalendar to a destination subcalendar.

    Preconditions:
    - item must belong to a subcalendar
    - destination must be different from source
    """
    src_subcal = item.parent_subcal
    assert src_subcal is not None, "Item does not belong to a subcalendar"
    assert src_subcal is not dst_subcal, "Source and destination are the same"

    record(editor, OpMoveItem(item.uid, src_subcal.uid, dst_subcal.uid))

    # Remove from source
    src_subcal.items.remove(item)
    src_subcal.items.sort(key=lambda i: i.sort_key())

    # Attach to destination
    item.parent_subcal = dst_subcal
    dst_subcal.items.append(item)
    dst_subcal.items.sort(key=lambda i: i.sort_key())


@contextmanager
def transaction(editor, label: str = ""):
    """
    Context manager for safely running a transaction.

    If an exception occurs, the transaction is discarded.
    Otherwise, it is committed to the undo stack.
    """
    begin_transaction(editor, label)
    try:
        yield
    except Exception:
        editor._current_tx = None
        raise
    else:
        commit_transaction(editor)
