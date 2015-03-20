#!usr/bin/python

import zulip
import requests
import json, os, sys

import timeconversions as TC
import delaymessage as DM

class DelayBot(object):

    def __init__(self, zulip_username, zulip_api_key, key_word, subscribed_streams=[]):
        """
        DelayBot takes a zulip username and api key,
        and a list of the zulip streams it should be active in.
        It keeps information used for parsing commands here
        """
        self.username = zulip_username
        self.api_key = zulip_api_key
        self.key_word = key_word.lower()

        self.subscribed_streams = subscribed_streams
        self.client = zulip.Client(zulip_username, zulip_api_key)
        self.subscriptions = self.subscribe_to_streams()
        self.streamNames = []
        for stream in self.subscriptions:
            self.streamNames.append(stream["name"])

        # keeps track of what unique id to give to new stored messages
        self.currentUid = 0

    @property
    def streams(self):
        """Standardizes a list of streams in the form [{'name': stream}]"""
        if not self.subscribed_streams:
            streams = [{"name": stream["name"]} for stream in self.get_all_zulip_streams()]
            return streams
        else: 
            streams = [{"name": stream} for stream in self.subscribed_streams]
            return streams

    def get_all_zulip_streams(self):
        """Call Zulip API to get a list of all streams"""

        response = requests.get("https://api.zulip.com/v1/streams", auth=(self.username, self.api_key))
        if response.status_code == 200:
            return response.json()["streams"]
        elif response.status_code == 401:
            raise RuntimeError("check your auth")
        else:
            raise RuntimeError(":( we failed to GET streams.\n(%s)" % response)


    def subscribe_to_streams(self):
        """Subscribes to zulip streams"""
        streams = self.streams
        self.client.add_subscriptions(streams)
        return streams
               

    def send_message(self, msg):
        """Sends a message to a zulip stream or private message"""

        if msg["type"] == "private":
            msg["to"] = msg["sender_email"]
        else:
            msg["to"] = msg["display_recipient"]

        message = {}
        for item in ["type", "subject", "to", "content"]:
            message[item] = msg[item]
        self.client.send_message(message)


    def parse_destination(self, content, msg, private):
        """Parses and returns the stream, topic, and messageOffset"""

        if private:
            stream = content[0].replace("_", " ")
            topic = content[1].replace("_", " ")
            messageOffset = 4
        else:
            stream = msg["display_recipient"]
            topic = msg["subject"]
            messageOffset = 2

        return stream, topic, messageOffset


    def respond(self, msg):
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        # DelayBot isn't allowed to call itself
        # because recursive calls could get messy
        if "delaybot" in msg["sender_full_name"].lower():
            return None

        content = msg["content"].split(" ")
        private = msg["type"] == "private"

        # intentional crash to speed up testing
        if len(content) >= 2 and content[1] == "crash":
            sys.exit()

        elif content[0].lower() == self.key_word:

            # if no command was given, it doesn't try to parse it
            if len(content) < 3 or (private and len(content) < 5):
                # ERROR! not enough commands given
                msg["content"] = "Not enough commands given!"
                self.send_message(msg)
                return None
            
            msg["content"], timestamp = TC.parse_time(content[1], msg["timestamp"])
            stream, topic, messageOffset = self.parse_destination(content[2:], msg, private)
            if stream not in self.streamNames:
                # ERROR! stream does not exist
                msg["content"] = "There is no stream known as %s" % stream
                return None

            message = " ".join([str(x) for x in content[messageOffset:]])
            dm = DM.delay_message(timestamp, msg["sender_full_name"],
                                self.currentUid, stream, topic, message)
            self.currentUid += 1
            self.send_message(msg)
            self.send_message(DM.create_message(dm))


    def check_file(self, time_file, current_time):
        pass


    def add_message_to_file(self, message):
        message_list = []
        if os.path.isfile('messages.json'):
            with open('messages.json', 'r+') as mfile:  #could do this using load function. refactor later
                json_string = mfile.read()
                message_list = DM.json_to_delay_messages(json_string)
                print 'found message json'
        message_list.append(message)
        sorted_list = sorted(message_list, key=lambda x:x.timestamp)
        with open('messages.json', 'w') as mfile:
            mfile.write(DM.delay_messages_to_json(sorted_list))   

        
    def remove_message_from_file(self, time_file):
        pass


    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""
        self.client.call_on_each_message(lambda msg: self.respond(msg))



zulip_username = os.environ['DELAYBOT_USR']
zulip_api_key = os.environ['DELAYBOT_API']
key_word = "DelayBot"
# an empty list will make it subscribe to all streams
subscribed_streams = ["test-bot"]

# won't run DelayBot when this file is imported
if __name__ == "__main__":
   new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
   new_bot.main()