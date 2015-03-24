#!usr/bin/python

# functions to handle time conversions

import re, time, datetime


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
    Returns unix time and the datetime it represents
    """

    time_dict = get_time(arg)
    time_delay = get_time_delay(time_dict, msg_time)
    unix = time.mktime(time_delay.timetuple())


    return unix, time_delay

def check_block_time(arg, time_dict):

    """Filters time for variable length block format"""

    arg = block_regexp_find.findall(arg)
    # used to check if all values are 0
    total = 0

    for value in arg:

        char = value[-1]
        if time_dict[char] != 0:
            raise ValueError("You defined the time for %s twice." % char)

        time_dict[char] = int(value[:-1])
        total += time_dict[char]
        if time_dict[char] > block_limits[char]:
            raise ValueError("%s is too high for %s in block format." % (time_dict[char], char))

    if total == 0:
        raise ValueError("You must specify at least one non-zero value.")

    return time_dict


def check_clock_time(arg, time_dict):
    """Filters time for 24hr and 12hr clocks, or single hours"""

    # clock times are in the format Hh:Mm(:Ss)[meridiem]
    # so the meridiem will always start at the 3rd character
    meridiem_point = 2
    if time_dict["format"] == "clock":
        arg = arg.split(":")
    elif time_dict["format"] == "single":
        # if the length is odd, that means that the hour is a single digit
        # and meridiem_point needs to account for that. ie 1am vs 12am
        meridiem_point -= len(arg) % 2
        # rest of function expects a list
        arg = [arg]
    time_dict["meridiem"] = arg[-1][meridiem_point:]
    arg[-1] = arg[-1][:meridiem_point]

    if time_dict["meridiem"] not in meridiems:
        raise ValueError("\"%s\" is not a meridiem." % time_dict["meridiem"])

    # specifies clock mode based on valid time_dict["meridiem"]
    # if no meridiem was given, it must be 24hr time
    # otherwise, it is 12hr time. either way, the limit must be right
    global clock_limits
    clock_limits[0] = 23 if time_dict["meridiem"] == "" else 12

    if len(arg) > 3:
        raise ValueError("Clock time must be Hh, Hh:Mm, or Hh:Mm:Ss.")

    for i, value in enumerate(arg):

        if not value.isdigit():
            if value:
                raise ValueError("You must give only numbers for time, not \"%s\"." % value)
            else:
                raise ValueError("You didn't specify any time for %s." % clock_format[i])

        value = int(value)
        if value > clock_limits[i]:
            raise ValueError("%s is too high for %s in clock format." % (value, clock_format[i]))
        time_dict[clock_format[i]] = value

    if time_dict["meridiem"] and time_dict["H"] == 0:
        raise ValueError("You cannot give zero for a 12hr clock H.")

    return time_dict


def get_time(arg):
    """
    Returns a dict of time formatted from arg, or None on invalid input
    Proper time formats and their limits:
        block: 1D24H60M60S
        clock (24hr): 23:59, 23:59:59
        clock (12hr): 12:59AM, 12:59:59P.M.
        single: 12AM, 12P.M.
    """

    time_dict = {"D": 0, "H": 0, "M": 0, "S": 0, "meridiem": "", "format": ""}

    arg = arg.upper()

    if block_regexp_match.match(arg):
        time_dict["format"] = "block"
    elif ":" in arg:
        time_dict["format"] = "clock"
    elif (arg[-2:] in meridiems or
            arg[-4:] in meridiems):
        time_dict["format"] = "single"
    else:
        raise ValueError("%s is not a valid format." % arg)

    if time_dict["format"] == "block":
        time_dict = check_block_time(arg, time_dict)
    elif time_dict["format"] in ("clock", "single"):
        time_dict = check_clock_time(arg, time_dict)

    print time_dict
    return time_dict


def get_time_delay(time_dict, msg_time):
    """
    Converts a given time to a datetime object at a later date
    uses the original zulip message timestamp for some calculations
    time_delay will be truncated to 11:59PM the next day if it goes over
    """

    msg_time = datetime.datetime.fromtimestamp(msg_time)
    print msg_time.timetuple()
    time_delay = None

    if time_dict["format"] == "block":
        delta = datetime.timedelta(days=time_dict["D"], hours=time_dict["H"],
                        minutes=time_dict["M"], seconds=time_dict["S"])
        time_delay = msg_time + delta

    elif time_dict["format"] in ("clock", "single"):

        if time_dict["H"] == 12:
            time_dict["H"] = 0
        if "P" in time_dict["meridiem"]:
            time_dict["H"] += 12

        time_delay = datetime(msg_time.year, msg_time.month,
                            msg_time.day, time_dict["H"], time_dict["M"], time_dict["S"])
        print time_delay.timetuple()
        if time_delay < msg_time:
            time_delay += timedelta(days=1)


    # gives a hard limit to how long it can delay until
    if time_delay.day > (msg_time.day + 1):
        time_delay = datetime(msg_time.year, msg_time.month,
                            msg_time.day + 1, 23, 59, 59)

    return time_delay