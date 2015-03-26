#!usr/bin/python

# functions to handle time conversions

from __future__ import unicode_literals

import re
import time
import datetime

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


def parse_time(user_time, zulip_time):
    """
    Handles parsing a given time message
    Returns a unix time, the date/time it represents,
    and the date/time of when the zulip message was sent
    """

    zulip_datetime = datetime.datetime.fromtimestamp(zulip_time)
    time_dict = get_time(user_time)
    time_delay = get_time_delay(time_dict, zulip_datetime)
    unix = time.mktime(time_delay.timetuple())

    return unix, str(time_delay), str(zulip_datetime)

def check_block_time(user_time, time_dict):
    """Filters time for variable length block format"""

    user_time = block_regexp_find.findall(user_time)
    # used to check if all values are 0
    total = 0

    for value in user_time:

        char = value[-1]
        if time_dict[char] != 0:
            raise ValueError("You defined the time for %s twice. Define it only once." % char)

        time_dict[char] = int(value[:-1])
        total += time_dict[char]
        if time_dict[char] > block_limits[char]:
            raise ValueError("%s is too high for the %s in block format." % (time_dict[char], char))

    if total == 0:
        raise ValueError("You must specify at least one non-zero value.")

    return time_dict


def check_clock_time(user_time, time_dict):
    """Filters time for 24hr, 12hr clocks, and single hours"""

    if time_dict["format"] == "clock":
        # clock times are in the format Hh:Mm(:Ss)[meridiem]
        # so the meridiem will always start at the 3rd character
        meridiem_point = 2
        user_time = user_time.split(":")
    elif time_dict["format"] == "single":
        # if the length is odd, that means that the hour is a single digit
        # and meridiem_point needs to account for that. ie 1am vs 12am
        meridiem_point = 2 - len(user_time) % 2
        # rest of function expects a list
        user_time = [user_time]

    if len(user_time) > 3:
        raise ValueError("Specific must be Hh[meridiem], Hh:Mm, or Hh:Mm:Ss.")

    time_dict["meridiem"] = user_time[-1][meridiem_point:]
    user_time[-1] = user_time[-1][:meridiem_point]
    if time_dict["meridiem"] not in meridiems:
        raise ValueError("\"%s\" is not a meridiem." % time_dict["meridiem"])
    # the hour limit must account for 12hr clock vs 23hr clock
    global clock_limits
    clock_limits[0] = 12 if time_dict["meridiem"] else 23

    for i, value in enumerate(user_time):
        if not value.isdigit():
            if value:
                raise ValueError("You must give only numbers for time, not \"%s\"." % value)
            else:
                raise ValueError("You didn't specify any time for the %s." % clock_format[i])

        value = int(value)
        if value > clock_limits[i]:
            raise ValueError("%s is too high for the %s." % (value, clock_format[i]))
        time_dict[clock_format[i]] = value

    if time_dict["meridiem"] and time_dict["H"] == 0:
        raise ValueError("You cannot give 0 for the H in 12hr or single format.")

    return time_dict


def get_time(user_time):
    """
    Returns a dict of time formatted from user_time, or None on invalid input
    Proper time formats and their limits:
        block: 1D24H60M60S
        clock (24hr): 23:59, 23:59:59
        clock (12hr): 12:59AM, 12:59:59P.M.
        single: 12AM, 12P.M.
    """

    time_dict = {"D": 0, "H": 0, "M": 0, "S": 0, "meridiem": "", "format": ""}

    user_time_caps = user_time.upper()
    print user_time

    if block_regexp_match.match(user_time_caps):
        time_dict["format"] = "block"
    elif ":" in user_time:
        time_dict["format"] = "clock"
    elif (user_time_caps[-2:] in meridiems or
            user_time_caps[-4:] in meridiems):
        time_dict["format"] = "single"
    else:
        raise ValueError("\"%s\" is not a valid time format. You might "
                        "have misentered a different command." % user_time)

    if time_dict["format"] == "block":
        time_dict = check_block_time(user_time_caps, time_dict)
    elif time_dict["format"] in ("clock", "single"):
        time_dict = check_clock_time(user_time_caps, time_dict)

    return time_dict


def get_time_delay(time_dict, zulip_datetime):
    """
    Converts a given time to a datetime object at a later date
    uses the original zulip message timestamp for some calculations
    time_delay will be truncated to 11:59PM the next day if it goes over
    """

    time_delay = None

    if time_dict["format"] == "block":
        delta = datetime.timedelta(days=time_dict["D"], hours=time_dict["H"],
                        minutes=time_dict["M"], seconds=time_dict["S"])
        time_delay = zulip_datetime + delta

    elif time_dict["format"] in ("clock", "single"):
        if time_dict["H"] == 12:
            time_dict["H"] = 0
        if "P" in time_dict["meridiem"]:
            time_dict["H"] += 12

        time_delay = datetime.datetime(zulip_datetime.year, zulip_datetime.month,
                            zulip_datetime.day, time_dict["H"], time_dict["M"], time_dict["S"])
        if time_delay < zulip_datetime:
            time_delay += datetime.timedelta(days=1)

    # gives a hard limit to how long it can delay until
    if time_delay.day > (zulip_datetime.day + 1):
        time_delay = datetime(zulip_datetime.year, zulip_datetime.month,
                            zulip_datetime.day + 1, 23, 59, 59)

    return time_delay
