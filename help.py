help_string = """
    DELAYBOT HELP:

    **Basic Commands**
        DelayBot queue --> show queued messages
        DelayBot unqueue <id> --> unqueue message with id
        DelayBot unqueue ALL  --> unqueue all messages
        DelayBot ping  --> delaybot are you there?
        DelayBot help  --> what you are reading now

    **Set up a Delayed Message:**
        Method A: Navigate to the Stream|Topic
        DelayBot <time> <message>    
        Method B: Send DelayBot a private message
        DelayBot <time> <stream> <topic> <message>

    **Accepted Formats**
        block: 1h3m2s  || 1d --> now + 1hr 3mins 2sec || now + 1day
        clock: 12:45pm || 8:45:59am
        24hr:  11:57   || 23:57:45
        single: 1pm    || 12am
        valid meridiems: am, a.m., AM, A.M.
"""