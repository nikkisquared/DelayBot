#!usr/bin/python
import json

class DelayMessage(object):

    def __init__(self, timestamp, user, uid, stream, topic, message):
        """
        Initializes an instance of a DelayMessage
        it needs a unix timestamp, username, unique id,
        stream:topic to respond in, and message to send
        """

        self.timestamp = timestamp
        self.user = user
        self.uid = uid
        self.stream = stream
        self.topic = topic
        self.message = message


    def create_message(self):
        """Creates a formatted message for Zulip"""

        message = {}
        message["type"] = "stream"
        message["display_recipient"] = self.stream
        message["subject"] = self.topic
        message["content"] = "%s\n- from [@**%s**]" % (self.message, self.user)
        return message

# def make_delay_message(timestamp, msg, message):
#     """Makes a delay message from a given timestamp, msg, and message"""
#     return DelayMessage(timestamp, msg["sender_full_name"])


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
