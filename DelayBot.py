#!usr/bin/python

from __future__ import unicode_literals

import zulip
import requests
import json
import os
import sys
import time

import database
import timeconversions as TC
import delaymessage
import help


class DelayBot(object):

    def __init__(self, zulip_username, zulip_api_key, key_word, subscribed_streams=[]):
        """
        DelayBot takes a Zulip username and API key,
        a key word to respond to (case insensitive),
        and a list of the Zulip streams it should be active in.
        """
        self.username = zulip_username
        self.api_key = zulip_api_key
        self.key_word = key_word.lower()

        self.subscribed_streams = subscribed_streams
        self.client = zulip.Client(zulip_username, zulip_api_key)
        self.subscriptions = self.subscribe_to_streams()
        self.stream_names = []
        for stream in self.subscriptions:
            self.stream_names.append(stream["name"])
        

    @property
    def streams(self):
        """Standardizes a list of streams in the form [{"name": stream}]"""
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
            raise RuntimeError("Failed to GET streams.\n(%s)" % response)


    def subscribe_to_streams(self):
        """Subscribes to Zulip streams"""
        streams = self.streams
        self.client.add_subscriptions(streams)
        return streams


    def register(self):
        """
        Keeps trying to register the bot until successful
        Returns queue_id and last_event_id on success
        """
        queue_id = None
        while queue_id == None:
            registration = self.client.register(json.dumps(["message"]))
            queue_id = registration.get("queue_id")
            last_event_id = registration.get("last_event_id")
        return queue_id, last_event_id


    def send_private_message(self, to, content):
        """Minimal requirements for sending a private message"""
        self.client.send_message({
            "type": "private",
            "to": to,
            "content": content
        })


    def parse_destination(self, content, msg, private): 
        """
        Parses and returns the stream and topic
        If the message is private, stream and topic must be user specified
        Otherwise, stream and topic can be taken from the msg metadata
        """
        if private:
            stream = content[2].replace("_", " ")
            topic = content[3].replace("_", " ")
        else:
            stream = msg["display_recipient"]
            topic = msg["subject"]

        return stream, topic


    def is_delaybot_call(self, content, sender):
        """
        Verifies whether or not a given message is directed to DelayBot
        Raises a ValueError if no commands were given
        """

        # recursion is denied
        if "delaybot" in sender.lower():
            return False
        if self.key_word in content[0].lower():
            # call is "DelayBot" with no following arguments
            if len(content) == 1:
                raise ValueError("You must specify a command when calling me.")
            # call looks like "DelayBot ..."
            else:
                return True
        # DelayBot was not referenced
        else:
            return False


    def is_valid_call(self, content, command, private):
        """
        Validates a given command to check if it can be parsed further
        Raises a ValueError on fatally incorrect inputs
        """

        activation_word = content[0].lower()
        content_length = len(content)
        unqueue_error = "You need to specify %s or `ALL`"
        time_error = ("Not enough commands given. You must specify "
                        "a delay time%s when calling me from %s.")

        # "delaybot (ping/help/queue)"
        if command in ("ping", "help", "queue"):
            return True

        elif command == "unqueue":
            # "delaybot unqueue" no id
            if content_length < 3:
                raise ValueError(unqueue_error % "`id`")
            # "delaybot unqueue [term]" where term is not a number or "ALL"
            elif not (content[2].isdigit() or content[2] == "ALL"):
                raise ValueError(unqueue_error % "a number")
            # "delaybot unqueue [number/ALL]"
            else:
                return True

        # "delaybot time message" but no stream and/or topic
        elif private and content_length < 5:
            raise ValueError(time_error % (", stream, topic, and message",
                            "a private message"))
        # "delaybot time" but no message
        elif content_length < 3:
            raise ValueError(time_error % (" and message ", "public streams"))
        # "delaybot time message" or "delaybot time steam topic message"
        else:
            return True
            

    def respond(self, msg):
        """
        Handles parsing commands, and calling other major functions
        to process them. Redirects output on success/fatally bad input
        """

        content = msg["content"].split(" ")
        sender = msg["sender_full_name"]
        private = msg["type"] == "private"
        # "DelayBot" is not neccesary to start off a private command
        if private and content[0].lower() != self.key_word:
            content = [self.key_word] + content

        if not self.is_delaybot_call(content, sender):
            return None
        command = content[1].lower()
        if not self.is_valid_call(content, command, private):
            return None

        if command == "ping":
            response = "I am on. What's up?"
        elif command == "help":
            response = help.help_string
        elif command == "queue":
            response = database.get_queue(sender)
        elif command == "unqueue":
            if content[2].isdigit():
                content[2] = int(content[2])
            response = database.unqueue(sender, content[2])
        else:
            response = self.parse_delay_message(content, msg, private)

        self.send_private_message(msg["sender_email"], response)


    def parse_delay_message(self, content, msg, private):
        """Write me"""

        timestamp, date, zulipdate = TC.parse_time(content[1], msg["timestamp"])
        stream, topic = self.parse_destination(content, msg, private)
        # "delaybot time stream topic message" with an non-existant stream
        if stream not in self.stream_names:
            raise ValueError("I am not in the stream \"%s\". Check capitals,"
                "spelling, and replace spaces with underscores." % stream)

        # a public command looks like "DelayBot [time] [message...]"
        message_offset = 2
        # but private commands include "[stream] [topic]"
        if private:
            message_offset = 4
        message = " ".join([x for x in content[message_offset:]])

        dm = delaymessage.make_delay_message(zulipdate, timestamp, date,
                        msg["sender_full_name"], stream, topic, message)
        database.add_message_to_db(dm)
        return "You have delayed a message to %s" % date


    def handle_error(self, e, sender):
        """Formats a given error message and sends it to the offending user"""

        error = e.message
        error = error.replace(" H", " Hour")
        error = error.replace(" M", " Minute")
        error = error.replace(" S", " Second")
        print error
        error += " If you want more details, you can call `DelayBot help`."
        self.send_private_message(sender, error)


    def main(self):
        """Write me"""

        # this both checks that DelayBot is on, and will create
        # the entire database and its' columns if it doesn't exist
        boot_message = delaymessage.make_delay_message(
            "(just now)", int(time.time()), "N/A", "DelayBot", "test-bot",
            "DelayBot" , "DelayBot is up and running")
        database.boot_db(boot_message)

        queue_id, last_event_id = self.register()

        while True:
            delta = time.time()

            dm = database.check_db(int(time.time()))
            if dm != None:
                msg = delaymessage.make_zulip_message(dm)
                self.client.send_message(msg)

            results = self.client.get_events(queue_id=queue_id,
                        last_event_id=last_event_id, dont_block=True)
            # for some reason, sometimes queue_id becomes wrong
            if results.get("events") == None:
                queue_id, last_event_id = self.register()
                for key, value in results:
                    print "key %s has value %s" % (key, value)
                continue

            for event in results["events"]:
                last_event_id = max(last_event_id, event["id"])
                try:
                    self.respond(event["message"])
                except ValueError as e:
                    self.handle_error(e, event["message"]["sender_email"])

            time.sleep(min(1, time.time() - delta))


# blocks DelayBot from running automatically when imported
if __name__ == "__main__":

    zulip_username = os.environ["DELAYBOT_USR"]
    zulip_api_key = os.environ["DELAYBOT_API"]
    key_word = "DelayBot"
    # an empty list will make it subscribe to all streams
    subscribed_streams = []

    new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
    new_bot.main()