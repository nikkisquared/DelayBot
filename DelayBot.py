#!usr/bin/python

import zulip
import requests
import json, os
import timeconversions
import DelayMessage as DM


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
        self.client.add_subscriptions(self.streams)


    def respond(self, msg):
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        # DelayBot isn't allowed to call itself
        # because recursive calls could get messy
        if "delaybot" in msg["sender_full_name"].lower():
            return None

        # there can be a variable number of arguments
        # so splitting them up gives a way to sort through them
        content = msg["content"].lower().split(" ")

        # if no command was given, it doesn't try to parse it
        if len(content) == 1:
            # ERROR! no command given
            return None

        elif content[0] == self.key_word:

            # intentional crash to speed up testing
            if len(content) >= 2 and content[1] == "crash":
                x = 5 / 0
            msg["content"] = self.parse_command(content[1:], msg["timestamp"])
            self.send_message(msg)
               

    def send_message(self, msg):
        """Sends a message to zulip stream"""

        self.client.send_message({
            "type": "stream",
            "subject": msg["subject"],
            "to": msg["display_recipient"],
            "content": msg["content"]
            })


    def parse_command(self, command, msgTime):
        """Parses a message to validate input"""

        output = u""

        output += command[0]
        time = timeconversions.get_time(command[0])
        if time:
            output += " is a proper time signature"
        else:
            output += " is not proper!!!! nope"
            return output

        delayTime = timeconversions.get_time_delay(time, msgTime)
        if delayTime:
            output += "\nYou have delayed to: %s" % delayTime



        return output


    def delay_message_to_json(self, delay_message):
        to_json = {
            "timestamp": delay_message.timestamp,
            "user":delay_message.user
            "uid":delay_message.uid
            "stream":delay_message.stream 
            "topic":delay_message.topic
            "message":delay_message.message
        }
        return json.dumps(to_json)

    def json_to_delay_messages(self, json):
        dict_list = json.load(json)
        message_list = (lambda x: DM.DelayMessage( x["timestamp"], x["user"], x["uid"],
                                        x["stream"], x["topic"], x["message"] ), dict_list)
        return message_list

    def check_file(self, time_file):
        pass 

    def add_message_to_file(self, time_file):
        pass
    
    def remove_message_from_file(self, time_file):
        pass

    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""
        self.client.call_on_each_message(lambda msg: self.respond(msg))


"""
    The Customization Part!
    
    Create a zulip bot under "settings" on zulip.
    Zulip will give you a username and API key
    key_word is the text in Zulip you would like the bot to respond to. This may be a 
        single word or a phrase.
    subscribed_streams is a list of the streams the bot should be active on. An empty 
        list defaults to ALL zulip streams
"""

zulip_username = os.environ['DELAYBOT_USR']
zulip_api_key = os.environ['DELAYBOT_API']
key_word = "DelayBot"
subscribed_streams = ["test-bot"]

if __name__ == "__main__":
   new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
   new_bot.main()