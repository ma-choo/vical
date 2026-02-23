# License: MIT

"""
Motions calculate and return ranges,
which are used to resolve selections and targets.
"""

from datetime import date, timedelta


class Motion:
    """
    Base class for motions. Holds the start and end of a motion.
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def normalized(self):
        """
        Return the motion as a (start, end) tuple
        and normalize start <= end.
        """
        return min(self.start, self.end), max(self.start, self.end)

    def apply(self, editor):
        """
        Update editor selection to reflect this motion.
        """
        raise NotImplementedError

    def __mul__(self, n: int):
        return self.scale(n)

    def __rmul__(self, n: int):
        return self.scale(n)

    def scale(self, n: int):
        raise NotImplementedError


class DateMotion(Motion):
    def expand(self):
        """
        Expand the date motion into a list of dates.
        """
        start, end = self.normalized()
        current = start
        dates = []
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def apply(self, editor):
        target_date = self.end
        editor.set_selected_date(target_date)

    @property
    def days(self):
        """
        Return the total number of days spanned by the motion.
        """
        start, end = self.normalized()
        return (end - start).days + 1

    def scale(self, n: int):
        delta = self.end - self.start
        new_end = self.start + (delta * n)
        return DateMotion(self.start, new_end)


class ItemMotion(Motion):
    def expand(self):
        """
        Expand item motion into a list of item indices.
        """
        start, end = self.normalized()
        return list(range(start, end + 1))

    def apply(self, editor):
        editor.selected_item_index = self.end

    def scale(self, n: int):
        delta = self.end - self.start
        new_end = self.start + (delta * n)
        return ItemMotion(self.start, new_end)


class Motions:
    """
    High-level motion factory class.
    Returns Motion objects.
    """
    def __init__(self, editor):
        self.editor = editor

    def date_move(self, delta_days: int):
        """
        Move selected_date by delta_days.
        Returns a DateMotion representing the movement.
        """
        start = self.editor.selected_date
        end = start + timedelta(days=delta_days)
        return DateMotion(start, end)

    def item_move(self, idx_delta: int):
        """
        Move selected_item_index by idx_delta within current day's items.
        Returns an ItemMotion representing the selection change.
        """
        items = self.editor.get_items_for_selected_date()
        idx = self.editor.selected_item_index

        if not items:
            return ItemMotion(0, 0)

        max_idx = len(items) - 1
        new_idx = max(0, min(idx + idx_delta, max_idx))

        return ItemMotion(idx, new_idx)

    def date_set(self, target_date: date):
        """
        Jump to a specific date.
        Returns a DateMotion from starting selected_date to target_date.
        """
        start = self.editor.selected_date
        end = target_date
        return DateMotion(start, end)
