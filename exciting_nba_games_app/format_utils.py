import datetime
from typing import List, Dict, Tuple

def format_clock(t) -> str:
    if t == '': # e.g. halftime or end of quarter/game
        t = '00:00'
    if len(t.split(':')) == 1: # e.g. 2.6 seconds remaining
        t = f"00:{int(t.split('.')[0]):02}"
    return t

def format_datetime(t) -> datetime.datetime:
    if t == '': # e.g. halftime or end of quarter/game
        t = '00:00'
    if len(t.split(':')) == 1: # e.g. 2.6 seconds remaining
        t = f"00:{int(t.split('.')[0]):02}"
    return datetime.datetime.strptime(t, '%M:%S').time()

def format_quarter(q) -> str:
    if q > 4:
        return str(q%4) + 'OT'
    else:
        return str(q)
