#!usr/bin/python

# functions to handle time conversions

import re, time
from datetime import *
import calendar

# hardcoded data information for verifying input

# time limits for block format: days, hours, minutes, seconds
block_limits = {'D': 1, 'H': 24, 'M': 60, 'S': 60}
regexp = "[0-9]{1,2}[HMDS]{1}"
# verifies block format
block_regexp_match = re.compile("^(%s){1,4}$" % regexp)
# filters parts out of block format
block_regexp_find = re.compile(regexp)

# valid meridiems (including none given)
meridiems = set(["AM", 'PM', "A.M.", "P.M.", ""])
# time limits for clock format: hours, minutes, seconds
clock_format = ["H", "M", "S"]
clock_limits = [23, 59, 59]


def parse_time(arg, msg_time):
    """
    Handles parsing a given time message
    Returns an output message and a unix timestamp,
    or an error explanation and None
    """

    output = u"%s" % arg

    time = get_time(arg)
    if time:
        output += " is a proper time signature"
    else:
        output += " is not proper!!!! nope"
        return output, None

    time_delay = get_time_delay(time, msg_time)
    unix = calendar.timegm(time_delay.utctimetuple())
    output += "\nYou have delayed to: %s" % time_delay
    output += "\nThe unix encoding for this is: %s" % unix

    return output, unix


def check_block_time(arg, time):
    """Filters time for variable length block format"""

    arg = block_regexp_find.findall(arg)
    # used to check if all values are 0
    total = 0

    for value in arg:

        char = value[-1]
        if time[char] != 0:
            # ERROR! already defined
            print "You defined a time twice!"
            return None

        time[char] = int(value[:-1])
        total += time[char]
        if time[char] > block_limits[char]:
            # ERROR! value too high for certain units
            print "Value for %s is too high!" %char
            return None

    if total == 0:
        # ERROR! all values given are 0
        print "You must specify at least one non-zero value"
        return None

    return time


def check_clock_time(arg, time):
    """Filters time for 24hr and 12hr clocks, or single hours"""

    # clock times are in the format Hh:Mm(:Ss)[meridiem]
    # so the meridiem will always start at the 3rd character
    meridiem_point = 2
    if time["format"] == "clock":
        arg = arg.split(":")
    elif time["format"] == "single":
        # if the length is odd, that means that the hour is a single digit
        # and meridiem_point needs to account for that. ie 1am vs 12am
        meridiem_point -= len(arg) % 2
        # rest of function expects a list
        arg = [arg]
    time["meridiem"] = arg[-1][meridiem_point:]
    arg[-1] = arg[-1][:meridiem_point]

    if time["meridiem"] not in meridiems:
        # ERROR! text at end that isn't a meridiem
        print "%s is not a meridiem" % time["meridiem"]
        return None

    # specifies clock mode based on valid time["meridiem"]
    # if no meridiem was given, it must be 24hr time
    # otherwise, it is 12hr time. either way, the limit must be right
    global clock_limits
    clock_limits[0] = 23 if time["meridiem"] == "" else 12

    if len(arg) < 1 or len(arg) > 3:
        # ERROR! missing values
        print "Clock time must be Hh or Hh:Mm or Hh:Mm:Ss"
        return None

    for i, value in enumerate(arg):

        if not value.isdigit():
            # ERROR! non-numeric value
            print "Non-numeric value!"
            return None

        if int(value) > clock_limits[i]:
            # ERROR! value too high
            print "Value for %s too high!" % time[clock_format[i]]
            return None

        time[clock_format[i]] = int(value)

    if time["meridiem"] and time["H"] == 0:
        # ERROR! no hour given for 12hr clock format
        print "You must give an hour from 1 to 12 for 12hr clock format"
        return None

    return time


def get_time(arg):
    """
    Returns a dict of time formatted from arg, or None on invalid input
    Proper time formats and their limits:
        block: 1D24H60M60S
        clock (24hr): 23:59, 23:59:59
        clock (12hr): 12:59AM, 12:59:59P.M.
        single: 12AM, 12P.M.
    """

    time = {"D": 0, "H": 0, "M": 0, "S": 0, "meridiem": "", "format": ""}

    arg = arg.upper()

    if block_regexp_match.match(arg):
        time["format"] = "block"
    elif ":" in arg:
        time["format"] = "clock"
    elif (arg[-2:] in meridiems or
            arg[-4:] in meridiems):
        time["format"] = "single"
    else:
        # ERROR! not a valid format
        print "Not a valid block or clock format!"
        return None

    if time["format"] == "block":
        time = check_block_time(arg, time)
    elif time["format"] in ("clock", "single"):
        time = check_clock_time(arg, time)

    print time
    return time


def get_time_delay(time, msg_time):
    """
    Converts a given time to a datetime object at a later date
    uses the original zulip message timestamp for some calculations
    time_delay will be truncated to 11:59PM the next day if it goes over
    """

    msg_time = datetime.fromtimestamp(msg_time)
    time_delay = None

    if time["format"] == "block":
        delta = timedelta(days=time["D"], hours=time["H"], 
                        minutes=time["M"], seconds=time["S"])
        time_delay = msg_time + delta

    elif time["format"] in ("clock", "single"):
        if time["H"] == 12:
            time["H"] = 0
        if "P" in time["meridiem"]:
            time["H"] += 12
        time_delay = datetime(msg_time.year, msg_time.month,
                            msg_time.day, time["H"], time["M"], time["S"])
        if time_delay < msg_time:
            time_delay += timedelta(days=1)

    # gives a hard limit to how long it can delay until
    if time_delay.day > (msg_time.day + 1):
        time_delay = datetime(msg_time.year, msg_time.month,
                            msg_time.day + 1, 23, 59, 59)

    return time_delay