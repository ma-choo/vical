# This file is part of vical.
# License: MIT (see LICENSE)

"""
Default key and command mapping.
"""

# Key consants:
BACKSPACE = 127
CTRL_A = 1
CTRL_B = 2
CTRL_C = 3
CTRL_D = 4
CTRL_E = 5
CTRL_F = 6
CTRL_G = 7
CTRL_H = 8
CTRL_I = 9
CTRL_J = 10
CTRL_K = 11
CTRL_L = 12
CTRL_M = 13
CTRL_N = 14
CTRL_O = 15
CTRL_P = 16
CTRL_Q = 17
CTRL_R = 18
CTRL_S = 19
CTRL_T = 20
CTRL_U = 21
CTRL_V = 22
CTRL_W = 23
CTRL_X = 24
CTRL_Y = 25
CTRL_Z = 26
CTRL_BSL = 28    # backslash
CTRL_RSB = 29    # right square bracket
CTRL_HAT = 30    # caret (^)
ESC = 27
ENTER = 10        # standard Enter (can also use 13 for carriage return if needed)
BACKSPACE = 127
SPACE = ord(' ')

# Flags
NV_NCH = 0x01 # may need to get a second char
NV_NCH_NOP = (0x02|NV_NCH) # get second char when no operator pending
NV_NCH_ALW = (0x04|NV_NCH) # always get a second char

NV_SS = 0x10 # may start selection
NV_SSS = 0x20 # may start selection with shift modifier
NV_STS = 0x40 # may stop selection without shift modif.
NV_RL = 0x80 # 'rightleft' modifies command
NV_KEEPREG = 0x100 # don't clear regname
NV_NCW = 0x200 # not allowed in command-line window


def init_default_keymap(cmds):
    keymap = {
        # CTRL_A: cmds.nv_addsub,
        # CTRL_B: cmds.nv_page,
        # CTRL_C: cmds.nv_esc,
        # CTRL_D: cmds.nv_halfpage,
        # CTRL_E: cmds.nv_scroll_line,
        # CTRL_F: cmds.nv_page,
        # CTRL_G: cmds.nv_ctrlg,
        # CTRL_H: cmds.nv_ctrlh,
        # CTRL_I: cmds.nv_pcmark,
        # CTRL_K: cmds.nv_error,
        # CTRL_L: cmds.nv_clear,
        # CAR: cmds.nv_down,
        CTRL_N: cmds.nv_date_down,
        # CTRL_O: cmds.nv_ctrlo,
        CTRL_P:   cmds.nv_date_up,
        # CTRL_Q: cmds.nv_visual,
        # CTRL_R: cmds.nv_redo_or_register,
        # CTRL_S: cmds.nv_ignore,
        # CTRL_T: cmds.nv_tagpop,
        # CTRL_U: cmds.nv_halfpage,
        # CTRL_V: cmds.nv_visual,
        # CTRL_W: cmds.nv_window,
        # CTRL_X: cmds.nv_addsub,
        # CTRL_Y: cmds.nv_scroll_line,
        # CTRL_Z: cmds.nv_suspend,
        # CTRL_BSL: cmds.nv_normal,
        # CTRL_RSB: cmds.nv_ident,
        # CTRL_HAT: cmds.nv_ungoto,
        # ENTER: cmds.nv_date_down,
        # BACKSPACE: cmds.nv_date_left,
        ESC: (cmds.nv_esc, 0),
        ' ': (cmds.nv_operator, 0),
        # '\'': cmds.nv_gomark,
        # '!': cmds.nv_operator,
        # '"': cmds.nv_regname,
        # '#': cmds.nv_hash,
        '$': (cmds.nv_week_end, 0),
        # '%': cmds.nv_percent,
        # '&': cmds.nv_optrans,
        # "'": cmds.nv_gomark,
        # '(': cmds.nv_bracket,
        # ')': cmds.nv_bracket,
        # '*': cmds.nv_indent,
        # '+': cmds.nv_date_down,
        # ',': cmds.nv_csearch,
        '-': (cmds.nv_date_up, 0),
        # '.': cmds.nv_dot,
        # '/': cmds.nv_search,
        ':': (cmds.nv_colon, 0),
        # ';': cmds.nv_csearch,
        # '<': cmds.nv_operator,
        # '=': cmds.nv_operator,
        # '>': cmds.nv_operator,
        # '?': cmds.nv_search,
        # '@': cmds.nv_at,
        # 'A': cmds.nv_edit,
        # 'B': cmds.nv_bck_word,
        'C': (cmds.nv_operator, 0),
        # 'D': cmds.nv_abbrev,
        # 'E': cmds.nv_wordcmd,
        # 'F': cmds.nv_csearch,
        'G': (cmds.nv_goto, 0),
        # 'H': cmds.nv_view_start,
        # 'I': cmds.nv_edit, enter item mode?
        # 'J': cmds.nv_join,
        # 'K': cmds.nv_ident,
        # 'L': cmds.nv_view_end,
        # 'M': cmds.nv_scroll,
        # 'N': cmds.nv_next,
        # 'O': cmds.nv_open,
        # 'P': cmds.nv_Put,
        # 'Q': cmds.nv_exmode,
        # 'R': cmds.nv_Replace,
        # 'S': cmds.nv_subst,
        'T': (cmds.nv_task, 0),
        # 'U': cmds.nv_Undo,
        # 'V': cmds.nv_visual,
        # 'W': cmds.nv_wordcmd,
        # 'X': cmds.nv_abbrev,
        # 'Y': cmds.nv_abbrev,
        # 'Z': cmds.nv_Zet,
        # '[': cmds.nv_brackets
        # '\\': cmds.nv_leader
        # ']': cmds.nv_brackets
        '^': (cmds.nv_week_start, 0),
        # '_': cmds.nv_single_unit_op,
        # '`': cmds.nv_gomark
        # 'a': cmds.nv_edit,
        # 'b': cmds.nv_bck_word,
        'c': (cmds.nv_operator, 0),
        'd': (cmds.nv_operator, 0),
        # 'e': cmds.nv_event,
        # 'f': cmds.nv_csearch,
        'g': (cmds.nv_g_cmd, NV_NCH),
        'h': (cmds.nv_date_left, 0),
        # 'i': cmds.nv_edit,
        'j': (cmds.nv_date_down, 0),
        'k': (cmds.nv_date_up, 0),
        'l': (cmds.nv_date_right, 0),
        # 'm': cmds.nv_mark,
        # 'n': cmds.nv_next,
        # 'o': cmds.nv_open,
        # 'p': cmds.nv_put,
        # 'q': cmds.nv_record,
        # 'r': cmds.nv_replace,
        # 's': cmds.nv_subst,
        't': (cmds.nv_task, 0),
        # 'u': cmds.nv_undo,
        # 'v': cmds.nv_visual,
        # 'w': cmds.nv_wordcmd,
        # 'x': cmds.nv_abbrev,
        'y': (cmds.nv_operator, 0),
        'z': (cmds.nv_zet, 0),
        # '{': cmds.nv_findpar,
        # '|': cmds.nv_pipe,
        # '}': cmds.nv_findpar,
        # '~': cmds.nv_tilde,
    }

    return keymap
    
def init_default_cmdmap(cmds):
    cmdmap = {
        "q": cmds.ex_quit,
        "quit": cmds.ex_quit,
        "q!": cmds.ex_quit_bang,
        "quit!": cmds.ex_quit_bang,
        "w": cmds.ex_write,
        "write": cmds.ex_write,
        "wq": cmds.ex_write_quit,
        "writequit": cmds.ex_write_quit,
    }

    return cmdmap
    