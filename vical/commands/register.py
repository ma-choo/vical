# License: MIT

"""
Functions for managing registers.
"""

from datetime import date, timedelta


class RegisterCmds:
    def __init__(self, editor):
        self.editor = editor

    def do_put(self, cmdargs):
        pass # TODO
        
    def build_item_from_payload(payload, start_date, target_subcal):
        pass # TODO

    def _insert_payload(self, payload, dates, target_subcal):
        # visual selection: events span visual selection
        if self._has_visual_selection():
            start_date = min(self.editor.visual_anchor_date, self.editor.selected_date)
            end_date = max(self.editor.visual_anchor_date, self.editor.selected_date)

            item = self.utils.build_item_from_payload(payload, start_date, target_subcal)

            # Adjust end_date for events if necessary
            if hasattr(item, "end_date"):
                duration = (item.end_date - item.start_date).days
                item.end_date = start_date + timedelta(days=duration)

            tx_insert_item(self.editor, item, target_subcal)
            return

        # No visual selection: iterate over resolved dates
        for d in dates:
            item = self.utils.build_item_from_payload(payload, d, target_subcal)
            tx_insert_item(self.editor, item, target_subcal)

    def _resolve_subcal(self, payload, use_original_subcal):
        """
        Returns the subcalendar for the item.
        - If payload contains original_subcal_uid, resolve it
        - Else use currently selected subcal
        """
        if original_subcal:
            uid = payload.get("original_subcal_uid")
            if uid:
                sc = self.editor.get_subcal_by_uid(uid)
                if sc:
                    return sc

        return self.editor.selected_subcal

    def _put_task():
        pass # TODO

    def _put_event():
        pass # TODO

class PutOperator(BaseOperator):
    def execute(self, motion=None, register=None, use_original_subcal=True, count=1, **kwargs):
        """
        Put items from a register.
        Handles visual selection and target dates.
        """
        dates = self._resolve_dates(motion, count)
        payloads = self.utils.get_register_payload(register or '"')

        if not payloads:
            return

        for payload in payloads:
            target_subcal = self._resolve_subcal(payload, use_original_subcal)
            self._insert_payload(payload, dates, target_subcal)

    def _insert_payload(self, payload, dates, target_subcal):
        # visual selection: events span visual selection
        if self._has_visual_selection():
            start_date = min(self.editor.visual_anchor_date, self.editor.selected_date)
            end_date = max(self.editor.visual_anchor_date, self.editor.selected_date)

            item = self.utils.build_item_from_payload(payload, start_date, target_subcal)

            # Adjust end_date for events if necessary
            if hasattr(item, "end_date"):
                duration = (item.end_date - item.start_date).days
                item.end_date = start_date + timedelta(days=duration)

            tx_insert_item(self.editor, item, target_subcal)
            return

        # No visual selection: iterate over resolved dates
        for d in dates:
            item = self.utils.build_item_from_payload(payload, d, target_subcal)
            tx_insert_item(self.editor, item, target_subcal)

    def _resolve_subcal(self, payload, use_original_subcal):
        """
        Returns the subcalendar for the item.
        - If payload contains original_subcal_uid, resolve it
        - Else use currently selected subcal
        """
        if original_subcal:
            uid = payload.get("original_subcal_uid")
            if uid:
                sc = self.editor.get_subcal_by_uid(uid)
                if sc:
                    return sc

        return self.editor.selected_subcal