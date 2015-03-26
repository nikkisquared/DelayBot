#!usr/bin/python

# methods for converting to and from a delay message

from __future__ import unicode_literals


def make_delay_message(dateStored, timestamp, date, user, stream, topic, message):
    """
    Creates an instance of a delaymessage with all data
    it needs a date when it was stored, unix timestamp, date,
    username, stream and topic to respond in, and message to send
    """
    return {
        "dateStored": dateStored,
        "timestamp": timestamp,
        "date": date,
        "user": user,
        "stream": stream,
        "topic": topic,
        "message": message
    }


def make_zulip_message(dm):
    """Converts a delaymessage into a public zulip message"""
    message = {}
    message["type"] = "stream"
    message["to"] = dm["stream"]
    message["subject"] = dm["topic"]
    message["content"] = "%s\n- from @**%s** at %s (EDT)" % (
            dm["message"], dm["user"], dm["dateStored"])
    return message