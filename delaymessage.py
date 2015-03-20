#!usr/bin/python
import json


def delay_message(timestamp, user, uid, stream, topic, message):
    """
    Creates an instance of a delaymessage with all data
    it needs a unix timestamp, username, unique id,
    stream:topic to respond in, and message to send
    """

    return {
        "timestamp": timestamp,
        "user": user,
        "uid": uid,
        "stream": stream, 
        "topic": topic,
        "message": message
    }


def create_message(dm):
    """Converts a delaymessage into a Zulip message"""

    message = {}
    message["type"] = u"stream"
    message["display_recipient"] = dm["stream"]
    message["subject"] = dm["topic"]
    message["content"] = u"%s\n- from @**%s**" % (dm["message"], dm["user"])
    print dm["stream"]
    print dm["topic"]
    return message


def dm_list_to_json(dm_list):  #move these later
    return json.dumps(dm_list)

def json_to_dm_list(from_json):
    return json.loads(from_json)