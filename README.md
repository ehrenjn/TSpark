# TSpark
A Python-based discord bot; A collaborative project between myself, and [@ehrenjn](https://github.com/ehrenjn)

## Running The Bot

1. Clone the repository:

```git clone https://github.com/amcpeake/TSpark```


2. Enter the new folder:

```cd ./TSpark```


3. Configure /storage/config.json with your own values. The ones given in the example config.json are necessary for operation


4. Start the bot:

```python ./TSpark.py```


## Command Glossary
### Command conventions:

[]  — A required parameter 

<> — An optional parameter 

= — A default value for a given parameter

#### !help — Lists available commands

### [Aidan's Commands](https://github.com/amcpeake/TSpark/blob/master/tony_modules/lego_funcs.py):


#### !download [link] <link2> ... — Downloads songs/albums/playlists from various sites. Currently supports:
* Bandcamp
* SoundCloud


#### !moji <OPTIONS = -l> [name] — Sends a moji
* -l — list available mojis
* -a [name] [link] — Add a moji
* -r [name] — Remove a moji


#### !discloud <OPTIONS = -l> <messageID> — Store and retrieve files
* -l — List all stored files and their indices
* -g [index] — Get a file given its index
* -s <messageID = ctx.message.id> — Store a file given a message id


#### !reminder <OPTIONS = -l> [reminder_text] [days|hours|minutes] — Set a reminder
* -u <user = ctx.author> — Set a reminder for a user
* -l — List all reminders


#### !nab <OPTIONS> [emoji] <emoji2> ... — Grab messages contained between last two instances of messages with given reactions'
* -c <#channel = ctx.channel> — Search in a given channel
* -n <all|num = 1000> — Search a given number of previous messages


#### !search <OPTIONS> [string] <-c [channel|all]> <-n [num|all]> <-u [user|all]> <-r [emoji]> — Search for messages
* -c <all|#channel = ctx.channel> — Set channel to search through
* -n <all|num = 1000> — Set number of messages to read
* -u <all|@user = ctx.author> — Set the user to read messages from
* -r [emoji] — Set the required reaction to be read

#### !joke — Tells a joke


#### !roll — Gives you your message ID as a "roll"


### [Ehren's Commands](https://github.com/ehrenjn/tony_spark_functions/blob/master/wak_funcs.py):


#### !eval [equation] — Evaluates a given equation


#### !play [STRING] — Adds a game for Tony to play


#### !unplay [STRING] — Removes a given game from Tony's list


#### !history — Dumps all messages from a channel into a .txt

