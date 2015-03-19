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
    """Creates a formatted message for Zulip"""

    message = {}
    message["type"] = u"stream"
    message["display_recipient"] = dm["stream"]
    message["subject"] = dm["topic"]
    message["content"] = u"%s\n- from @**%s**" % (dm["message"], dm["user"])
    return message


def delay_messages_to_json(delay_message_list):
    to_json_list = []
    for dm in delay_message_list:
        to_json = {
            "timestamp": dm.timestamp,
            "user":dm.user,
            "uid":dm.uid,
            "stream":dm.stream, 
            "topic":dm.topic,
            "message":dm.message
        }
        to_json_list.append(to_json)
    return json.dumps(to_json_list)

def json_to_delay_messages(from_json):
    dict_list = json.loads(from_json)
    message_list = map(lambda x: DelayMessage( x["timestamp"], x["user"], x["uid"],
                                    x["stream"], x["topic"], x["message"] ), dict_list)
    return message_list

