# License: MIT (see LICENSE)

"""
Registers store yanked calendar items in a way that supports rotation and
delayed resolution at paste time.

Registers store payloads, not live objects. 
Payloads are snapshots of essential data required for paste operations.
This avoids accidental mutations and allows the paste logic to decide how to 
instantiate a new CalendarItem.
"""

from dataclasses import dataclass
from typing import Literal, Iterable, List

from vical.core.subcalendar import CalendarItem, Task, Event


class Register:
    def __init__(self):
        self._regs = {
            '"': [],    # unnamed
            '0': [],    # yank register
            '-': [],    # small delete
            **{str(i): [] for i in range(1, 10)},    # 1-9 delete history
            **{chr(c): [] for c in range(ord('a'), ord('z') + 1)},  # a-z
        }

        self._previous = None

    def write(self, regname: str, items, rotate=False):
        if regname == "_": # Black hole register
            return

        regname, append = self._normalize_regname(regname)

        if not isinstance(items, Iterable) or isinstance(items, (Task, Event)):
            items = [items]

        payloads = [calitem_to_register(item) for item in items]

        # Always update unnamed register
        self._regs['"'] = payloads.copy()

        # Yank: also update register 0
        if not rotate:
            self._regs['0'] = payloads.copy()

        # Delete: rotate numbered registers
        if rotate:
            for i in range(9, 1, -1):
                self._regs[str(i)] = self._regs[str(i - 1)].copy()
            self._regs['1'] = payloads.copy()

        # Handle named registers (a–z)
        if regname in self._regs:
            if append:
                self._regs[regname].extend(payloads)
            else:
                self._regs[regname] = payloads.copy()

        self._previous = regname

    def get(self, regname='"'):
        """
        Returns a list of RegisterPayload objects,
        which can then be converted back into CalendarItem instances at paste.
        """
        regname, _ = self._normalize_regname(regname)
        return self._regs.get(regname, []).copy()

    def clear(self, regname='"'):
        """
        Clear a register by setting its value to an empty list.
        """
        regname, _ = self._normalize_regname(regname)
        self._regs[regname] = []

    def _normalize_regname(self, regname: str):
        if regname.isupper():
            return regname.lower(), True
        return regname, False


@dataclass(frozen=True)
class RegisterPayload:
    """
    Immutable snapshot of a CalendarItem.
    Holds essential fields needed to reconstruct the item at paste time
    """
    kind: Literal["task", "event"] 
    data: dict


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
                ),
            },
        )
    elif item.TYPE == "event":
        return RegisterPayload(
            kind="event",
            data={
                "name": item.name,
                # Event start and end dates are set at paste,
                # but we preserve the original dates in the payload so we
                # can use the event's duration property for smart paste.
                "start_date": item.start_date,
                "end_date": item.end_date,
                # store original subcal uid so we can resolve it later
                "original_subcal_uid": (
                    item.parent_subcal.uid if item.parent_subcal else None
                ),
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
            tdate=None,  # date is resolved on paste
            completed=payload.data.get("completed", False),
            deadline=payload.data.get("deadline"),
            parent_subcal=None,  # resolved on paste
        )

    if payload.kind == "event":
        return Event(
            uid=None,
            name=payload.data["name"],
            start_date=payload.data["start_date"],
            end_date=payload.data["end_date"],
            parent_subcal=None,
        )

    raise ValueError(f"Unsupported payload kind: {payload.kind}")
