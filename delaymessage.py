#!usr/bin/python

from __future__ import unicode_literals


def delay_message(timestamp, date, user, stream, topic, message):
    """
    Creates an instance of a delaymessage with all data
    it needs a unix timestamp, date, username,
    stream:topic to respond in, and message to send
    """

    return {
        "timestamp": timestamp,
        "date": date,
        "user": user,
        "stream": stream,
        "topic": topic,
        "message": message
    }


def create_message(dm):
    """Converts a delaymessage into a Zulip message"""

    message = {}
    message["type"] = "stream"
    message["display_recipient"] = dm["stream"]
    message["subject"] = dm["topic"]
    message["content"] = "%s\n- from @**%s**" % (dm["message"], dm["user"])
    print dm["stream"]
    print dm["topic"]
    return message