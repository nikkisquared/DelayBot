#!usr/bin/python

import zulip
import requests
import psycopg2
import dataset
import json, os, sys, time

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


    def parse_destination(self, content, msg, private): 
        """
        Parses and returns the stream and topic
        If the message is private, stream and topic must be user specified
        Otherwise, stream and topic can be taken from the msg metadata
        """

        if private:
            stream = content[0].replace("_", " ")
            topic = content[1].replace("_", " ")
        else:
            stream = msg["display_recipient"]
            topic = msg["subject"]

        return stream, topic


    def respond(self, msg):  #EH: this method needs serious refactoring
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        content = msg["content"].split(" ")
        private = (msg["type"] == "private")

        # keyword must be used in message, and
        # delaybot doesn"t call itself to prevent recursion glitches
        if (content[0].lower() != self.key_word or 
            "delaybot" in msg["sender_full_name"].lower()):
            return None

        # private calls need to add a stream and topic name
        # public calls need to give a delay time and message
        if len(content) < 3 or (private and len(content) < 5):
            if private:
                raise ValueError("Not enough commands given. You must "
                        "specify a delay time, stream, topic, and message.")
            raise ValueError("Not enough commands given. You must "
                        "specify a delay time and message.")

        stream, topic = self.parse_destination(content[2:], msg, private)
        if stream not in self.stream_names:
            raise ValueError("There is no stream \"%s\"." % stream)

        # variable renaming needed?
        # nikki here: yeah this is not ideal, see my note below
        msg["content"], timestamp = TC.parse_time(content[1], msg["timestamp"])
        # this refers to the start position of the message to be sent
        message_offset = 2
        if private: message_offset += 2
        message = " ".join([str(x) for x in content[message_offset:]])
        dm = DM.delay_message(timestamp, msg["sender_full_name"],
                            self.currentUid, stream, topic, message)
        self.currentUid += 1
        # we should not be editing raw message throughout, create a new one
        # nikki here: I know, I want to implement an error system instead
        # of clumsily editing messages. this will do for now though...
        self.send_message(msg) 
        #self.add_message_to_db(dm)


    def check_db(self, unix_timestamp=int(time.time()) ):

        with dataset.connect() as db:
            results = db.query("SELECT * FROM messages WHERE timestamp<%s"%unix_timestamp)
            for result in results:
                msg = DM.create_message(result)
                self.send_message(msg)
                self.remove_message_from_db(result)
            # for res in db["messages"].all(): 
            #     print [ (x, res[x]) for x in res.keys()]


    def add_message_to_db(self, delay_message):
        with dataset.connect() as db:
            db["messages"].insert(delay_message)
            db.commit()


    def remove_message_from_db(self, result):
        with dataset.connect() as db:
            db["messages"].delete(id=result["id"])
            db.commit()


    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""

        registration = self.client.register(json.dumps(["message"]))
        queue_id = registration["queue_id"]
        last_event_id = registration["last_event_id"]

        self.lazy_hack_function_for_time_differences(queue_id,last_event_id)

        while True:

            results = self.client.get_events(queue_id=queue_id, 
                        last_event_id=last_event_id, dont_block=True)
            if results.get("events") == None:
                continue

            for event in results["events"]:

                last_event_id = max(last_event_id, event["id"])
                if "message" in event.keys():
                    try:
                        self.respond(event["message"])
                    except ValueError as e:
                        error = e.message
                        error = error.replace(" H", " Hour")
                        error = error.replace(" M", " Minute")
                        error = error.replace(" S", " Second")
                        print error
                        event["message"]["content"] = error
                        self.send_message(event["message"]) 

                    print event["message"]["timestamp"]

            #print int(time.time()) 
            #self.check_db()
            

    def lazy_hack_function_for_time_differences(self, queue_id, last_event_id):
        """
        there is a discrepancy between the timestamp from time.time() and that on messages.
        As timeconversions module will require refactoring (for instance it has problems with
        its namespace usage - time module etc...) here is a little module that highlights there is no difference.
        """
        test_message = {
        "type": "private",
        "sender_email": "delaybot-bot@students.hackerschool.com",
        "content": time.time(),
        "subject": "lazy_hack"
        }
        self.send_message(test_message)
        returned_messages = self.client.get_events(queue_id=queue_id, 
                            last_event_id=last_event_id, dont_block=True)
        zulipstamp = returned_messages["events"][-1]["message"]["timestamp"]
        print zulipstamp, time.time(), zulipstamp-time.time(), test_message["content"]


zulip_username = os.environ["DELAYBOT_USR"]
zulip_api_key = os.environ["DELAYBOT_API"]
key_word = "DelayBot"
# an empty list will make it subscribe to all streams
subscribed_streams = ["test-bot"]

# won"t run DelayBot when this file is imported
if __name__ == "__main__":
   new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
   new_bot.main()