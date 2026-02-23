# License: MIT (see LICENSE)

"""
An Op is a single, atomic mutation to a calendar or calendar item.
A transaction is a list of Ops.
"""

from contextlib import contextmanager
from functools import wraps


class Op:
    """Base class for all operations."""
    def apply(self, editor):
        raise NotImplementedError

    def revert(self, editor):
        raise NotImplementedError


class OpSetItemAttr(Op):
    def __init__(self, item_uid: str, attr: str, old, new):
        self.item_uid = item_uid
        self.attr = attr
        self.old = old
        self.new = new

    def apply(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        assert item is not None
        setattr(item, self.attr, self.new)

    def revert(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        assert item is not None
        setattr(item, self.attr, self.old)


class OpInsertItem(Op):
    def __init__(self, subcal_uid: str, item):
        self.subcal_uid = subcal_uid
        self.item = item

    def apply(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        self.item.parent_subcal = sc
        sc.items.append(self.item)
        sc.items.sort(key=lambda i: i.sort_key())

    def revert(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        sc.items.remove(self.item)
        self.item.parent_subcal = None
        sc.items.sort(key=lambda i: i.sort_key())


class OpRemoveItem(Op):
    def __init__(self, subcal_uid: str, item):
        self.subcal_uid = subcal_uid
        self.item = item

    def apply(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        sc.items.remove(self.item)
        self.item.parent_subcal = None
        sc.items.sort(key=lambda i: i.sort_key())

    def revert(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        self.item.parent_subcal = sc
        sc.items.append(self.item)
        sc.items.sort(key=lambda i: i.sort_key())


class OpMoveItem(Op):
    def __init__(self, item_uid: str, src_uid: str, dst_uid: str):
        self.item_uid = item_uid
        self.src_uid = src_uid
        self.dst_uid = dst_uid

    def apply(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        src = editor.get_subcal_by_uid(self.src_uid)
        dst = editor.get_subcal_by_uid(self.dst_uid)
        assert item and src and dst

        src.items.remove(item)
        src.items.sort(key=lambda i: i.sort_key())

        item.parent_subcal = dst
        dst.items.append(item)
        dst.items.sort(key=lambda i: i.sort_key())

    def revert(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        src = editor.get_subcal_by_uid(self.src_uid)
        dst = editor.get_subcal_by_uid(self.dst_uid)
        assert item and src and dst

        dst.items.remove(item)
        dst.items.sort(key=lambda i: i.sort_key())

        item.parent_subcal = src
        src.items.append(item)
        src.items.sort(key=lambda i: i.sort_key())


class OpSetSubcalAttr(Op):
    def __init__(self, subcal_uid: str, attr: str, old, new):
        self.subcal_uid = subcal_uid
        self.attr = attr
        self.old = old
        self.new = new

    def apply(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        setattr(sc, self.attr, self.new)

    def revert(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None
        setattr(sc, self.attr, self.old)


class OpInsertSubcal(Op):
    def __init__(self, index: int, subcal):
        self.index = index
        self.subcal = subcal

    def apply(self, editor):
        editor.subcalendars.insert(self.index, self.subcal)

    def revert(self, editor):
        editor.subcalendars.remove(self.subcal)


class OpRemoveSubcal(Op):
    def __init__(self, index: int, subcal):
        self.index = index
        self.subcal = subcal

    def apply(self, editor):
        editor.subcalendars.remove(self.subcal)

    def revert(self, editor):
        editor.subcalendars.insert(self.index, self.subcal)


class Transaction:
    _next_id = 1

    def __init__(self, label: str = ""):
        self.id = Transaction._next_id
        Transaction._next_id += 1
        self.ops: list[Op] = []
        self.label = label

    def apply(self, editor):
        for op in self.ops:
            op.apply(editor)

    def revert(self, editor):
        for op in reversed(self.ops):
            op.revert(editor)


def begin_transaction(editor, label=""):
    if editor.history.current_tx is not None:
        raise RuntimeError("Nested transactions are not allowed")
    editor.history.current_tx = Transaction(label)


def record(editor, op: Op):
    tx = editor.history.current_tx
    if tx is None:
        raise RuntimeError("record() called outside of transaction")
    tx.ops.append(op)


def commit_transaction(editor):
    tx = editor.history.current_tx
    if tx is None:
        return

    if tx.ops:
        editor.history.undo_stack.append(tx)
        editor.history.redo_stack.clear()

        if len(editor.history.undo_stack) > editor.settings.max_history:
            editor.history.undo_stack.pop(0)

    editor.history.current_tx = None


def rollback_transaction(editor):
    editor.history.current_tx = None


@contextmanager
def transaction_block(editor, label=""):
    begin_transaction(editor, label)
    try:
        yield
    except Exception:
        rollback_transaction(editor)
        raise
    else:
        commit_transaction(editor)


def tx_set_item_attr(editor, item, attr, new):
    old = getattr(item, attr)
    if old == new:
        return

    record(editor, OpSetItemAttr(item.uid, attr, old, new))
    setattr(item, attr, new)


def tx_insert_item(editor, subcal, item):
    assert item.parent_subcal is None

    record(editor, OpInsertItem(subcal.uid, item))

    item.parent_subcal = subcal
    subcal.items.append(item)
    subcal.items.sort(key=lambda i: i.sort_key())


def tx_remove_item(editor, item):
    subcal = item.parent_subcal
    assert subcal is not None

    record(editor, OpRemoveItem(subcal.uid, item))

    subcal.items.remove(item)
    item.parent_subcal = None
    subcal.items.sort(key=lambda i: i.sort_key())


def tx_move_item(editor, item, dst_subcal):
    src_subcal = item.parent_subcal
    assert src_subcal is not None
    assert src_subcal is not dst_subcal

    record(editor, OpMoveItem(item.uid, src_subcal.uid, dst_subcal.uid))

    src_subcal.items.remove(item)
    src_subcal.items.sort(key=lambda i: i.sort_key())

    item.parent_subcal = dst_subcal
    dst_subcal.items.append(item)
    dst_subcal.items.sort(key=lambda i: i.sort_key())


def tx_set_subcal_attr(editor, subcal, attr, new):
    old = getattr(subcal, attr)
    if old == new:
        return

    record(editor, OpSetSubcalAttr(subcal.uid, attr, old, new))
    setattr(subcal, attr, new)


def tx_insert_subcal(editor, subcal):
    assert subcal not in editor.subcalendars

    index = len(editor.subcalendars)
    record(editor, OpInsertSubcal(index, subcal))
    editor.subcalendars.append(subcal)


def tx_remove_subcal(editor, subcal):
    assert subcal in editor.subcalendars

    index = editor.subcalendars.index(subcal)
    record(editor, OpRemoveSubcal(index, subcal))
    editor.subcalendars.remove(subcal)


def tx_undo(editor):
    if not editor.history.undo_stack:
        return False
    tx = editor.history.undo_stack.pop()
    tx.revert(editor)
    editor.history.redo_stack.append(tx)
    return tx


def tx_redo(editor):
    if not editor.history.redo_stack:
        return False
    tx = editor.history.redo_stack.pop()
    tx.apply(editor)
    editor.history.undo_stack.append(tx)
    return tx