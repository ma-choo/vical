# utils.py - date/time utility functions
import calendar
from datetime import date, datetime

def contains_bad_chars(name: str) -> bool:
    invalid_chars = {'\t', '\n', '\r', '\x1b', ',', '<', '>', ':', '"', '/', '\\', '|'}
    if any(ch in invalid_chars for ch in name):
        return True
    if any(ord(ch) < 32 for ch in name):  # check for ascii control chars
        return True
    return False
    
def get_day_name(index: int) -> str:
    return calendar.day_abbr[(index + 6) % 7] # shift so sunday = 0

def get_month_name(month: int) -> str:
    if 1 <= month <= 12:
        return calendar.month_abbr[month]
    else:
        raise ValueError(f"Invalid month number: {month}")

def get_first_day_offset(month, year):
    return calendar.monthrange(year, month)[0] + 1