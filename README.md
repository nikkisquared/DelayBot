DelayBot
========
DelayBot is a Zulip bot by `nikkisquared` and `condnsdmatters` (https://github.com/condnsdmatters/DelayBot) that allows users to create scheduled Zulip messages. It can be called from public channels and private messages, although it gives all replies in private. Some ideas for uses are self-reminders, calling other bots, pre-announcing something in case you forget to later. DelayBot was started from the source code for Bot-Builder https://github.com/di0spyr0s/Bot-Builder


Usage
=====
**Basic Commands**  
DelayBot queue --> show queued messages  
DelayBot unqueue <id\> --> unqueue message with id  
DelayBot unqueue ALL  --> unqueue all messages  
DelayBot ping  --> delaybot are you there?  
DelayBot help  --> gives you this text
replies are always private messages- please keep most DB calls there
also, saying "DelayBot" is not necessary from a private message

**Delay A Message**  
Method A: Navigate to the Stream|Topic  
`DelayBot <time> <message>`  
Method B: Send DelayBot a private message  
`(DelayBot) <time> <stream> <topic> <message>`  
streams or topics with spaces need to be replaced with underscores  
ie DelayBot <time\> 455\_Broadway hey\_everyone <message\>  

**Accepted <time\> Formats**  
block:  1h45m30s  || 1d --> now + 1hr 45mins 30sec || now + 1day  
24hr:   08:45:59  || 23:45  
12hr:   8:45:59am || 12:45pm  
single: 8am       || 12pm  
valid meridiems: am, a.m., AM, A.M.
note that DelayBot uses Eastern Time, as Recurse Center is in New York