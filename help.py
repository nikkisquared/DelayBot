#!usr/bin/python

# stores the lengthy help_string that explains usage

help_string = """
    Basic Commands
        DelayBot queue --> show queued messages
        DelayBot unqueue <id> --> unqueue message with id
        DelayBot unqueue ALL  --> unqueue all messages
        DelayBot ping  --> delaybot are you there?
        DelayBot help  --> what you are reading now

    Delay A Message:
        Method A: Navigate to a stream and topic
            DelayBot <time> <message>
        Method B: Send DelayBot a private message
            (DelayBot) <time> <stream> <topic> <message>
        streams or topics with spaces need to be replaced with underscores
        ie DelayBot <time> 455_Broadway hey_everyone <message>

    Accepted <time> Formats
        block:  1h45m30s  || 1d --> now + 1hr 45mins 30sec || now + 1day
        24hr:   08:45:59  || 23:45
        12hr:   8:45:59am || 12:45pm
        single: 8am       || 12pm
        valid meridiems: am, a.m., AM, A.M.
"""