#!usr/bin/python

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
        message["type"] = u"stream"
        message["display_recipient"] = self.stream
        message["subject"] = self.topic
        message["content"] = u"%s\n- from @**%s** " % (self.message, self.user)
        return message