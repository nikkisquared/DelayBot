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
        """Parses and returns the stream, topic, and message_offset"""

        if private:
            stream = content[0].replace("_", " ")
            topic = content[1].replace("_", " ")
            message_offset = 4
        else:
            stream = msg["display_recipient"]
            topic = msg["subject"]
            message_offset = 2

        return stream, topic, message_offset


    def respond(self, msg):  #EH: this method needs serious refactoring
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        content = msg["content"].split(" ")
        private = (msg["type"] == "private")
        

        if content[0].lower() == self.key_word:
            
            stream, topic, message_offset = self.parse_destination(content[2:], msg, private)

            if "delaybot" in msg["sender_full_name"].lower(): #delaybot doesn't call itself
                return None

            elif len(content) < 3 or (private and len(content) < 5): #delaybot checks command length
                msg["content"] = "Not enough commands given!" 
                self.send_message(msg)
                return None
                           
            elif stream not in self.streamNames: #delaybot checks valid stream destination
                msg["content"] = "There is no stream known as %s" % stream 
                self.send_message(msg)
                return None
                
            else:
                msg["content"], timestamp = TC.parse_time(content[1], msg["timestamp"])  #variable renaming needed?

                message = " ".join([str(x) for x in content[message_offset:]])  #this is unclear?
                dm = DM.delay_message(timestamp, msg["sender_full_name"],
                                    self.currentUid, stream, topic, message)
                
                self.currentUid += 1
                
                self.send_message(msg)
                self.add_message_to_db(dm)




    def check_db(self, unix_timestamp=int(time.time()) ):

        with dataset.connect() as db:
            results = db.query('SELECT * FROM messages WHERE timestamp<%s'%unix_timestamp)
            for result in results:
                msg = DM.create_message(result)
                self.send_message(msg)
                self.remove_message_from_db(result)
            for res in db['messages'].all(): 
                print [ (x, res[x]) for x in res.keys()]

    def add_message_to_db(self, delay_message):
        with dataset.connect() as db:
            db['messages'].insert(delay_message)
            db.commit()

    def remove_message_from_db(self, result):
        with dataset.connect() as db:
            db['messages'].delete(id=result['id'])
            db.commit()

    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""
        registration = self.client.register(json.dumps(["message"]))
        queue_id = registration["queue_id"]
        last_event_id = registration["last_event_id"]

        while True:
            results = self.client.get_events(queue_id=queue_id,last_event_id=last_event_id, dont_block=True)
            for event in results['events']:
                last_event_id = max(last_event_id, event['id'])
                if "message" in event.keys():
                    self.respond(event["message"])                    
            print int(time.time())
            self.check_db()
            

zulip_username = os.environ['DELAYBOT_USR']
zulip_api_key = os.environ['DELAYBOT_API']
key_word = "DelayBot"
# an empty list will make it subscribe to all streams
subscribed_streams = ["test-bot"]

# won't run DelayBot when this file is imported
if __name__ == "__main__":
   new_bot = DelayBot(zulip_username, zulip_api_key, key_word, subscribed_streams)
   new_bot.main()