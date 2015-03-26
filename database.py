#!usr/bin/python

# functions for interacting with the database

import psycopg2
import dataset


def boot_db(boot_message):
    """Write me"""
    with dataset.connect() as db:
        db['messages'].insert(boot_message)


def get_queue(user):
    """Write me"""

    content = ""
    with dataset.connect() as db:
        for m in db["messages"].find(user=user, order_by="date"):
            content += ("\t%s.\t\t  %s\t %s"
                "\t%s|%s   ||   %s\n " % (
                m["id"], m["dateStored"], m["date"], 
                m["stream"], m["topic"], m["message"]))

    if not content:
        content = "You have no messages queued."
    else:
        content = ("\tID.\t From Date\t\t Time\t  To Date\t\tTime"
                    "\t\tStream|Topic\t\t||\tMessage \n" + content)
    return content


def unqueue(user, del_id):
    """Write me"""

    dropped = 0

    with dataset.connect() as db:
        for m in db['messages'].find(user=user):
            if m['id'] == del_id or del_id == 'ALL':
                remove_message_from_db(m)
                dropped += 1

    if dropped == 0:
        return "You have nothing queued with that ID."
    else:
        plural = min(dropped -1, 1)
        return "Successfully unqueued your message%s!" % ("s" * plural)


def check_db(unix_timestamp):
    """
    Checks if any delay_messages need to be sent
    Returns the first one found, or None
    """

    with dataset.connect() as db:
        results = db.query("SELECT * FROM messages WHERE timestamp<%d" % unix_timestamp)
        for result in results:
            remove_message_from_db(result)
            db.commit()
            delay_message = result
            print delay_message
            return delay_message
    return None


def add_message_to_db(delay_message):
    """Adds a formatted delay_message to the database"""
    with dataset.connect() as db:
        db["messages"].insert(delay_message)
        for res in db["messages"].all():
            print [ (x, res[x]) for x in res.keys()]
        db.commit()


def remove_message_from_db(result):
    """Removes a given, existing entry from the database"""
    with dataset.connect() as db:
        db["messages"].delete(id=result["id"])
        db.commit()