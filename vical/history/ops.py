# ops.py - Operations for history tracking
# This file is part of vical.
# License: MIT (see LICENSE)

"""
This module defines the primitive operations (ops) used by the undo/redo
history system.

Each op represents a single, atomic mutation to editor state.
Ops track old state and new state, so theyknow how to apply
themselves and how to revert themselves.

Transactions group multiple Ops into a single undoable action.
"""

from contextlib import contextmanager


class Op:
    """
    Base class for all operations.
    """
    def apply(self, editor):
        raise NotImplementedError

    def revert(self, editor):
        raise NotImplementedError


class OpSetAttr(Op):
    """
    Represents a change to a single attribute on a calendar item.
    """
    def __init__(self, item_uid: str, attr: str, old, new):
        self.item_uid = item_uid
        self.attr = attr
        self.old = old
        self.new = new

    def apply(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        assert item is not None, f"Item {self.item_uid} not found"
        setattr(item, self.attr, self.new)

    def revert(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        assert item is not None, f"Item {self.item_uid} not found"
        setattr(item, self.attr, self.old)


class OpInsertItem(Op):
    """
    Represents an item being inserted into a subcalendar.
    """
    def __init__(self, subcal_uid: str, item):
        self.subcal_uid = subcal_uid
        self.item = item

    def apply(self, editor):
        sc = editor.get_subcal_by_uid(self.subcal_uid)
        assert sc is not None, f"Subcalendar {self.subcal_uid} not found"

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
    """
    Represents an item being removed from a subcalendar.
    """
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
    """
    Represents an item moving from one subcalendar to another.
    """
    def __init__(self, item_uid: str, src_uid: str, dst_uid: str):
        self.item_uid = item_uid
        self.src_uid = src_uid
        self.dst_uid = dst_uid

    def apply(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        src = editor.get_subcal_by_uid(self.src_uid)
        dst = editor.get_subcal_by_uid(self.dst_uid)

        assert item is not None
        assert src is not None
        assert dst is not None

        src.items.remove(item)
        src.items.sort(key=lambda i: i.sort_key())

        item.parent_subcal = dst
        dst.items.append(item)
        dst.items.sort(key=lambda i: i.sort_key())

    def revert(self, editor):
        item = editor.get_item_by_uid(self.item_uid)
        src = editor.get_subcal_by_uid(self.src_uid)
        dst = editor.get_subcal_by_uid(self.dst_uid)

        assert item is not None
        assert src is not None
        assert dst is not None

        dst.items.remove(item)
        dst.items.sort(key=lambda i: i.sort_key())

        item.parent_subcal = src
        src.items.append(item)
        src.items.sort(key=lambda i: i.sort_key())
