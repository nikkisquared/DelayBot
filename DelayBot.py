#!usr/bin/python

import zulip
import requests
import psycopg2
import dataset
import json, os, sys
import time

import timeconversions as TC
import delaymessage as DM


class DelayBot(object):

    def __init__(self, zulip_username, zulip_api_key, key_word, subscribed_streams=[]):
        """
        DelayBot takes a zulip username and api key,
        a key word to respond to (case insensitive),
        and a list of the zulip streams it should be active in
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

        # keeps track of what unique id to give to new stored messages
        self.currentUid = 0


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


    def send_private_message(self, to, content):
        """Simple wrapper for sending a private message on zulip"""
        self.client.send_message({
            "type": u"private",
            "to": to,
            "content": content
        })


    def parse_destination(self, content, msg, private): 
        """
        Parses and returns the stream and topic, if there is any to get
        If the message is private, stream and topic must be user specified
        Otherwise, stream and topic can be taken from the msg metadata
        """

        if not private:
            stream = msg["display_recipient"]
            topic = msg["subject"]
        elif len(content) < 4:
            stream = ""
            topic = ""
        else:
            stream = content[2].replace("_", " ")
            topic = content[3].replace("_", " ")

        return stream, topic


    def is_valid_message(self, content, sender, private, stream):
        """
        Validates a given command to check if it can be parsed further
        Raises a ValueError on fatally incorrect inputs
        """

        activation_word = content[0].lower()
        command_terms = len(content)
        terms_error = "Not enough commands given. You must specify a delay time"

        if activation_word != self.key_word:
            return False
        elif "delaybot" in sender.lower():
            return False
        elif private and command_terms < 5:
            raise ValueError(terms_error + ", stream, topic, and message "
                            "when calling me from a private message.")
        elif command_terms < 3:
            raise ValueError(terms_error + " and message when calling me "
                            "from public streams.")
        elif stream not in self.stream_names:
            raise ValueError("There is no stream \"%s\"." % stream) 
        else:
            return True
            

    def respond(self, msg):  
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        content = msg["content"].split(" ")
        private = (msg["type"] == "private")
        stream, topic = self.parse_destination(content, msg, private)
        
        if self.is_valid_message(content, msg["sender_full_name"], private, stream):

            timestamp, date = TC.parse_time(content[1], msg["timestamp"])
            user_response = u"You have delayed a message to %s" % date

            # this refers to the start position of the message to be sent
            message_offset = 2
            if private: message_offset += 2
            message = " ".join([str(x) for x in content[message_offset:]])
            dm = DM.delay_message(timestamp, msg["sender_full_name"],
                                self.currentUid, stream, topic, message)
            self.currentUid += 1

            self.send_private_message(msg["sender_email"], user_response)
            self.add_message_to_db(dm)


    def check_db(self, unix_timestamp):
        print unix_timestamp
        with dataset.connect() as db:
            results = db.query("SELECT * FROM messages WHERE timestamp<%d" % unix_timestamp)
            #print results
            for result in results:
                print result
                msg = DM.create_message(result)
                self.send_message(msg)
                self.remove_message_from_db(result)
            db.commit()


    def add_message_to_db(self, delay_message):
        with dataset.connect() as db:
            db["messages"].insert(delay_message)
            for res in db["messages"].all():
                print [ (x, res[x]) for x in res.keys()]
            db.commit()


    def remove_message_from_db(self, result):
        with dataset.connect() as db:
            db["messages"].delete(id=result["id"])
            db.commit()


    def handle_error(self, e, sender):
        """Handles everything with a given error to print it, and send it to the user"""

        error = e.message
        error = error.replace(" H", " Hour")
        error = error.replace(" M", " Minute")
        error = error.replace(" S", " Second")
        print error
        self.send_private_message(sender, error + u"")


    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""

        queue_id = None
        registration = self.client.register(json.dumps(["message"]))
        queue_id = registration.get("queue_id")
        last_event_id = registration.get("last_event_id")

        while True:
            results = self.client.get_events(queue_id=queue_id, 
                        last_event_id=last_event_id, dont_block=True)
            for event in results["events"]:
                last_event_id = max(last_event_id, event["id"])

                if "message" in event.keys():
                    try:
                        self.respond(event["message"])
                    except ValueError as e:
                        self.handle_error(e, event["message"]["sender_email"])

            now = int(time.time())
            self.check_db(now)


zulip_username = os.environ["DELAYBOT_USR"]
zulip_api_key = os.environ["DELAYBOT_API"]
key_word = "DelayBot"
# an empty list will make it subscribe to all streams
subscribed_streams = ["test-bot"]

# won't run DelayBot when this file is imported
if __name__ == "__main__":
   new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
   new_bot.main()