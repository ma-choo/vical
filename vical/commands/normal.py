# License: MIT

"""
Normal/Visual mode command pipeline.
"""

from datetime import date, timedelta

from vical.commands.calendar import CalendarCmds
from vical.commands.cmdargs import Mode
from vical.commands.motions import Motions, DateMotion, ItemMotion
from vical.commands.operators import Operators, OpArgs
from vical.commands.utils import UtilCmds


class NormalCmds:
    def __init__(self, editor, utils):
        self.editor = editor
        self.utils = utils
        self.motions = Motions(editor)
        self.operators = Operators(editor)
        # self.regcmds = RegisterCmds(editor)
        self.calcmds = CalendarCmds(editor, utils)

    def nv_esc(self, cmdargs):
        self.utils.reset_editor(cmdargs)

    def nv_date_left(self, cmdargs):
        """
        Move date selection left (1 day back).
        """
        delta = -1
        cmdargs.motion = self.motions.date_move(delta)
        self._handle_motion(cmdargs)

    def nv_date_right(self, cmdargs):
        """
        Move date selection right (1 day forward).
        """
        delta = 1
        cmdargs.motion = self.motions.date_move(delta)
        self._handle_motion(cmdargs)

    def nv_date_up(self, cmdargs):
        delta = -7
        cmdargs.motion = self.motions.date_move(delta)
        self._handle_motion(cmdargs)

    def nv_date_down(self, cmdargs):
        delta = 7
        cmdargs.motion = self.motions.date_move(delta)
        self._handle_motion(cmdargs)

    def nv_item_up(self, cmdargs):
        delta = -1
        cmdargs.motion = self.motions.item_move(delta)
        self._handle_motion(cmdargs)

    def nv_item_down(self, cmdargs):
        delta = 1
        cmdargs.motion = self.motions.item_move(delta)
        self._handle_motion(cmdargs)

    def nv_g_cmd(self, cmdargs):
        """
        Commands that start with "g".
        """
        # "gg": goto
        if cmdargs.next_key == 'g':
            self.nv_goto(cmdargs)
        # "g0": beginning of week
        elif cmdargs.next_key == '0':
            self.nv_week_start(cmdargs)
        # "gk": item up
        elif cmdargs.next_key == 'k':
            self.nv_item_up(cmdargs)
        # "gj": item down
        elif cmdargs.next_key == 'j':
            self.nv_item_down(cmdargs)

    def nv_goto(self, cmdargs):
        """
        Vim-style Goto command.
        """
        # Use the count buffer as the date string
        date_str = cmdargs.count_buffer
        cmdargs.count_buffer = ""

        # "gg": Goto beginning of month
        if not date_str:
            return self.nv_month_start(cmdargs)
        # "0gg": Goto today.
        if date_str == "0":
            target_date = date.today()
        # "<COUNT>gg": Parse the count as a date and goto that date
        # e.g., "10312026gg": goto October 10, 2026
        else:
            target_date = self.utils.parse_date_string(date_str)

        if not target_date:
            return

        # Record date for ungoto
        cmdargs.last_date_before_goto = self.editor.selected_date

        cmdargs.motion = self.motions.date_set(target_date)
        self._handle_motion(cmdargs)

    def nv_ungoto(self, cmdargs):
        last_date = cmdargs.last_date_before_goto
        if not last_date:
            return
        else:
            target_date = last_date
            cmdargs.last_date_before_goto = self.editor.selected_date
            cmdargs.motion = self.motions.date_set(target_date)
            self._handle_motion(cmdargs)

    def nv_month_start(self, cmdargs):
        d = self.editor.selected_date
        target_date = date(d.year, d.month, 1)
        cmdargs.motion = self.motions.date_set(target_date)
        self._handle_motion(cmdargs)

    def nv_month_end(self, cmdargs):
        d = self.editor.selected_date

        if d.month == 12:
            next_month = date(d.year + 1, 1, 1)
        else:
            next_month = date(d.year, d.month + 1, 1)

        target_date = next_month - timedelta(days=1)
        cmdargs.motion = self.motions.date_set(target_date)
        self._handle_motion(cmdargs)

    def nv_week_start(self, cmdargs):
        d = self.editor.selected_date
        week_start = self.editor.settings.week_start
        delta = (d.weekday() - week_start) % 7
        target_date = d - timedelta(days=delta)

        cmdargs.motion = self.motions.date_set(target_date)
        self._handle_motion(cmdargs)

    def nv_week_end(self, cmdargs):
        d = self.editor.selected_date
        week_start = self.editor.settings.week_start
        week_end = (week_start + 6) % 7
        delta = (week_end - d.weekday()) % 7
        target_date = d + timedelta(days=delta)

        cmdargs.motion = self.motions.date_set(target_date)
        self._handle_motion(cmdargs)

    def _handle_motion(self, cmdargs):
        """
        Motion handler for operator-pending or motion-pending commands.
        """
        if cmdargs.count_buffer:
            cmdargs.motion_count = int(cmdargs.count_buffer)
            cmdargs.count_buffer = ""
        motion = cmdargs.motion * cmdargs.motion_count
        if not motion:
            return

        # Clear cross-type visual anchors and selection
        if isinstance(motion, DateMotion):
            self.editor.visual_anchor_item_index = None
        elif isinstance(motion, ItemMotion):
            self.editor.visual_anchor_date = None
            self.editor.selected_item_index = 0

        motion.apply(self.editor) # Apply selection to editor

        # Motion-pending command
        if cmdargs.motion_pending_cmd:
            cmdargs.motion_pending_cmd(cmdargs)
            cmdargs.motion_pending_cmd = None
            return

        # Operator-pending
        if cmdargs.op_pending_key:
            self._execute_operator_motion(cmdargs)
            return

        # Plain motion
        cmdargs.motion = None

    def nv_operator(self, cmdargs):
        """
        Operator key handling.
        """
        key = cmdargs.key

        # Immediately execute on visual selection
        if cmdargs.op_pending_key is None and self.editor.visual_active:
            self._execute_selection_operator(cmdargs)
            return

        # Single-unit operator
        # Analogous to Vim's linewise operators (dd, yy, etc)
        # Uppercase or space execute on one keypress
        if (
            cmdargs.op_pending_key == key
            or key.isupper()
            or key == ' '
        ):
            self._execute_single_unit_operator(cmdargs)
            return

        # Enter operator-pending
        cmdargs.op_pending_key = key
        cmdargs.op_count = int(cmdargs.count_buffer) if cmdargs.count_buffer else 1
        cmdargs.count_buffer = ""

    def _execute_single_unit_operator(self, cmdargs):
        """
        Operate on the selected item.
        """
        item = self.editor.selected_item
        if not item:
            return
        opargs = OpArgs(
            op_key=cmdargs.key,
            target_items=[item],
            regname=cmdargs.regname,
        )
        self.operators.do_operator(opargs)
        cmdargs.clear()

    def _execute_operator_motion(self, cmdargs):
        """
        Operate on items in a motion range.
        """
        motion = cmdargs.motion

        # op_count + motion multiplies the range of the motion by op_count
        if cmdargs.op_count:
            motion = motion * total_count

        items = self.editor.get_items_in_motion(motion)

        opargs = OpArgs(
            op_key=cmdargs.op_pending_key,
            target_items=items,
            regname=cmdargs.regname,
        )
        self.operators.do_operator(opargs)
        cmdargs.clear()

    def _execute_selection_operator(self, cmdargs):
        """
        Operate on items in the visual selection range.
        """
        items=self.editor.get_items_in_visual_selection()
        opargs = OpArgs(
            op_key=cmdargs.key,
            target_items=items,
            regname=cmdargs.regname,
        )
        self.operators.do_operator(opargs)
        cmdargs.clear()

    def single_unit_op(self, cmdargs):
        if cmdargs.op_pending_key is None:
            self._execute_single_unit_operator(cmdargs)

    def nv_task(self, cmdargs):
        """
        Creating new tasks.
        """
        if cmdargs.op_pending_key:
            return

        # Extract count
        count = int(cmdargs.count_buffer) if cmdargs.count_buffer else 0
        cmdargs.count_buffer = ""

        # If there's a count, wait for a motion
        if count:
            cmdargs.special_count = count
            cmdargs.motion_pending_cmd = self._execute_task_motion
        # Otherwise, create a single task
        else:
            self._execute_single_task(cmdargs)

    def _execute_single_task(self, cmdargs):
        """
        Create a single new task on the selected date.
        """
        name = cmdargs.input_text or "New Task"
        date = self.editor.selected_date
        subcal = self.editor.selected_subcal

        self.calcmds.do_create_tasks(
            dates=[date],
            name=name,
            subcal=subcal
        )

    def _execute_task_motion(self, cmdargs):
        """
        Create multiple instances of a task in motion intervals.
        e.g., 3T5l = create 3 instances of a tasks in intervals of 5 days.
        """
        motion = cmdargs.motion
        if not isinstance(motion, DateMotion): # Only DateMotion makes sense
            cmdargs.motion_pending_cmd = None
            return

        repeats = cmdargs.special_count or 1
        dates = self.utils.motion_to_date_interval(
            motion,
            repeats
        )

        subcal = self.editor.selected_subcal
        name = cmdargs.input_text or "New Task"

        self.calcmds.do_create_tasks(
            dates=dates,
            name=name,
            subcal=subcal
        )

        cmdargs.clear()

    def nv_event(self, cmdargs):
        """
        Creating new events.
        """
        pass # TODO

    def _execute_single_event(self, cmdargs):
        """
        Create a single new event spanning the selection range.
        """
        pass # TODO

    def _execute_event_motion(self, cmdargs):
        """
        Create multiple single-day events in motion intervals.
        """
        pass # TODO

    def nv_colon(self, cmdargs):
        self.utils.change_mode(cmdargs, Mode.EX_CMD)
        """
        Normal-mode handler for ":".

        Vical should three conceptual behaviors:

        1) If Visual mode is active:
        Treat ":" as an operator over the visual selection.

        2) If an operator is pending:
        Treat ":" as a motion target (operator-motion bifurcation).

        3) If a count is provided (e.g. 3:):
        Convert count into a line/date range before entering command-line mode.

        4) Otherwise:
        Enter command-line (Ex) mode and execute the command.
        """

        editor = self.editor

        # ------------------------------------------------------------
        # CASE 1: VISUAL MODE ACTIVE
        # ------------------------------------------------------------
        # In Vim:
        #     V + :   runs Ex command over selected range.
        #
        # In your system:
        # - You likely want to transform the current visual selection
        #   into a date interval or item set.
        # - Then feed that as a range into your Ex command parser.
        #
        # This should:
        #   - NOT clear cmdargs yet.
        #   - Route through your executor or ex-layer.
        # ------------------------------------------------------------
        if editor.visual_active:
            # TODO:
            # 1. Resolve visual selection into a date range or item set.
            # 2. Store it in cmdargs.range or similar.
            # 3. Transition UI into command-line mode.
            #
            # Example:
            # cmdargs.range = editor.get_visual_range()
            # self.enter_command_mode(cmdargs)
            return


        # ------------------------------------------------------------
        # CASE 2: OPERATOR PENDING
        # ------------------------------------------------------------
        # Example:
        #     d:
        #
        # Here ":" behaves like a MOTION.
        #
        # In Vim this becomes a characterwise exclusive motion.
        #
        # In your architecture:
        # - This should create a motion object.
        # - Assign it to cmdargs.motion.
        # - Let your normal motion resolution pipeline handle it.
        #
        # IMPORTANT:
        # This should NOT execute Ex immediately.
        # It should feed back into your operator-resolution path.
        # ------------------------------------------------------------
        if cmdargs.op_pending_key:
            # TODO:
            # Create a motion object representing
            # "line range to be determined by Ex command"
            #
            # Example conceptual motion:
            # cmdargs.motion = ExRangeMotion()
            #
            # Then pass control to motion handler:
            # self._handle_motion(cmdargs)
            return


        # ------------------------------------------------------------
        # CASE 3: COUNT PREFIX (e.g. 3:)
        # ------------------------------------------------------------
        # In Vim:
        #     3:
        # expands to:
        #     :.,.+2
        #
        # Meaning:
        #   current_line to current_line + (count - 1)
        #
        # In your calendar context:
        # You may want:
        #   current_date → current_date + (count - 1)
        #
        # This is a design choice:
        # - Should count affect Ex range?
        # - Or should Ex commands handle count explicitly?
        #
        # If you support it:
        #   - Convert count into a date interval
        #   - Store as cmdargs.range
        # ------------------------------------------------------------
        if cmdargs.op_count:
            # TODO:
            # Convert count into date interval.
            #
            # Example:
            # start = editor.selected_date
            # end = start + timedelta(days=cmdargs.op_count - 1)
            # cmdargs.range = (start, end)
            #
            # IMPORTANT:
            # Do NOT clear cmdargs yet.
            pass


        # ------------------------------------------------------------
        # CASE 4: ENTER COMMAND-LINE (EX) MODE
        # ------------------------------------------------------------
        # This is the default behavior of ":".
        #
        # Responsibilities:
        # - Tell UI to open command line buffer.
        # - Suspend normal-mode key parsing.
        # - Collect input string.
        # - Pass command string to Ex executor.
        #
        # Architecture boundary:
        #   UI collects string
        #   Executor executes
        #   Editor mutates
        #
        # After execution:
        #   - If command failed → abort operator (if any)
        #   - If command succeeded → finalize and clear cmdargs
        #
        # DO NOT call cmdargs.clear() here unconditionally.
        # Clearing should happen at the executor boundary.
        # ------------------------------------------------------------
        # Example conceptual flow:

        # 1. Enter command mode
        # self.ui.enter_command_mode() TODO can't access ui here

        # 2. UI will collect input and later call:
        #    self.executor.execute_ex(cmd_string, cmdargs)
        #
        # The executor should:
        #   - Use cmdargs.range if present
        #   - Handle failures
        #   - Clear cmdargs at the correct lifecycle boundary

    def nv_zet(cmdargs):
        """
        Commands that start with "z".
        """
        # "zc": Hide the selected subcalendar.
        match cmdargs.next_key:
            case 'c':
                self.editor.selected_subcal.toggle_hidden()
    