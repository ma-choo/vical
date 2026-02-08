# This file is part of vical.
# License: MIT (see LICENSE)

"""
Registers store yanked calendar items in a way 
that supports rotation, unnamed vs numbered registers, and delayed resolution 
at paste time.

Registers store payloads, not live objects. 
Payloads are snapshots of essential data required for paste operations.
This avoids accidental mutations and allows the paste logic to decide how to 
instantiate a new CalendarItem.

Like Vim:
  The unnamed register (") always holds the most recently yanked item.
  Numbered registers 1-9 rotate on each yank if use_numbered=True.
"""

from dataclasses import dataclass
from typing import Literal

from vical.core.subcalendar import CalendarItem, Task, Event


class Register:
    def __init__(self):
        """
        Initialize the register system.
        
        " is the unnamed register.
        1-9 are numbered registers used for rotation.
        """
        self.named = {
            '"': None, # unnamed register
            **{str(i): None for i in range(1, 10)} # numbered registers
        }

    def set(self, item, use_numbered=True):
        """
        Create a payload from a calendar item and store it in the registers.
        """
        payload = calitem_to_register(item)  # create a payload snapshot
        self.named['"'] = payload  # store in the unnamed register

        if use_numbered: # rotate the numbered registers
            # shift numbered registers up:
            for i in range(9, 1, -1):
                self.named[str(i)] = self.named.get(str(i - 1))
            # put the newest payload in register 1
            self.named['1'] = payload

    def get(self, key='"'):
        """
        Retrieve a payload from a register.
        Returns the stored payload, which can then be converted back into
        a CalendarItem at paste.
        """
        return self.named.get(key)

    def clear(self, key='"'):
        """
        Clear a register by setting its value to None.
        """
        self.named[key] = None


@dataclass
class RegisterPayload:
    """
    Immutable snapshot of a CalendarItem for storage in a register.
    """
    kind: Literal["task", "event"] # indicates the type of item.
    data: dict # essential fields needed to reconstruct the item at paste time


def calitem_to_register(item) -> RegisterPayload:
    """
    Convert a calendar item to a register payload.
    """
    if item.TYPE == "task":
        return RegisterPayload(
            kind="task",
            data={
                "name": item.name,
                "completed": item.completed,
                "deadline": item.deadline,
                # At paste, we can either paste to the selected subcal or the
                # item's original subcal.
                # We store the original subcal uid so we can resolve it later
                # if needed.
                "original_subcal_uid": (
                    item.parent_subcal.uid if item.parent_subcal else None
                )
            },
        )
    elif item.TYPE == "event":
        return RegisterPayload(
            kind="event",
            data={
                "name": item.name,
                # Event start and end dates are set at paste,
                # but we preserve the original dates in the payload so we
                # can use the events duration property for smart paste.
                "start_date":item.start_date,
                "end_date":item.end_date,
                # store original subcal uid so we can resolve it later
                "original_subcal_uid": (
                    item.parent_subcal.uid if item.parent_subcal else None
                )
            },
        )
    raise ValueError(f"Unsupported calendar item type: {item.TYPE}")


def calitem_from_register(payload: RegisterPayload) -> CalendarItem:
    """
    Convert a register payload to a calendar item.
    """
    if payload.kind == "task":
        return Task(
            uid=None,
            name=payload.data["name"],
            tdate=None, # date is resolved on paste
            completed=payload.data.get("completed", False),
            deadline=payload.data.get("deadline"),
            parent_subcal=None, # resolved on paste
        )
    if payload.kind == "event":
        return Event(
            uid=None,
            name=payload.data["name"],
            start_date=payload.data["start_date"],
            end_date=payload.data["end_date"],
            parent_subcal=None,
        )