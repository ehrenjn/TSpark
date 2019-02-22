#A file containing all of wak's functions for tony spark
#Might be broken into a bunch of files if the bot gets bloated

import requests
import random
import re
import discord
import asyncio
from .util import JSONStore #relative import means this wak_funcs.py can only be used as part of the tony_modules package now
import os
from pathlib import Path
import io
from TSpark import CONFIG

STORAGE_FILE = os.path.join(os.environ['TONYROOT'], 'storage', 'wak_storage.json')


class WakStore(JSONStore):
    def __init__(self):
        super().__init__(STORAGE_FILE)
        if self['playables'] is None: #init playables so I don't have to keep checking if they're None
            self['playables'] = []
        

def setup(bot):

    storage = WakStore()

    @bot.command(name = "eval")
    async def execute(ctx, *, cmd): #if cmd arg is keyword only it lets discordpy know to pass in args as one string
        import random #import locally because I don't want eval to have global namespace
        import math
        import re
        try:
            return_val = str(eval(cmd, locals())) #only executes expressions, not statements.
            #ALSO: FOR SOME UNGODLY REASON eval WILL NOT CONSERVE locals IF YOU HAVE NESTED SCOPE
            #ie, eval("[math.sin(x) for x in range(10)]", None, locals()) WILL FAIL BECAUSE WHEN YOU DO LIST COMPREHENSION YOU CREATE A NESTED SCOPE, AND FOR SOME REASON THAT NESTED SCOPE IS EMPTY. IT DOESN'T CONTAIN locals
            #BUT NOTICE THAT THIS WILL ONLY BREAK FOR LOCAL SCOPE. SO ALL YOUR VARIABLES HAVE TO BE DEFINED IN GLOBAL SCOPE
            #THAT'S WHY IM PASSING IN locals() WHERE IM SUPPOSED TO BE PASSING IN globals()!!!!!!
            #ALSO BE AWARE THAT WHEN YOU USE eval OUTSIDE OF A FUNCTION AND DON'T SPECIFY ANY SCOPE PARAMS IT'LL USE THE CORRECT LOCAL AND GLOBAL SCOPES BY DEFAULT, AND LOCAL SCOPE WILL BE EQUAL TO GLOBAL SCOPE SO IT'LL ALL WORK OUT
            #THIS MEANS THAT I ALSO COULD HAVE IMPORTED THE MODULES OUTSIDE OF THE FUNCTION AND PASSED NO PARAMS INTO eval, HOWEVER THEN ALL MY GLOBALS WOULD BE AVAILABLE IN THE CALL TO eval WHICH WOULD BE A BIT OF A MESS
        except BaseException as e:
            return_val =  "{}: {}".format(e.__class__.__name__, e)
        if len(return_val) > 2000:
            await ctx.send("Sorry, the return value's too long to send")
        else:
            await ctx.send(return_val)

    @bot.command()
    async def img(ctx, *args):
        query = '+'.join(args) + '&source=lnms&tbm=isch'
        url = 'https://www.google.ca/search?q=' + query
        data = requests.get(url).content.decode(errors = 'ignore')
        imgs = re.findall(r'src="(https://encrypted-tbn0\.gstatic\.com/images.+?)"', data)
        if len(imgs) == 0:
            await ctx.send('No images found')
        else:
            embed = discord.Embed()
            embed.set_image(url = random.choice(imgs))
            await ctx.send(embed = embed)

    @bot.command()
    async def play(ctx, *, cmd):
        if len(cmd) <= 128:
            storage['playables'].append(cmd)
            storage.update()
            await bot.change_presence(activity = discord.Game(name = cmd))
            await ctx.send('added playable')
        else:
            await ctx.send("Playable wasn't added because it was > 128 chars long")

    @bot.command()
    async def restart(ctx, *args):
        if ctx.channel.id == 513536262507069443:
            await ctx.send("Rebooting...") #I would bot.close() but then it tries to cancel the ctx.send or something and throws an error which in turn stops the restart corutine so I ain't gonna bother
            os.system(". ~/Python/tony_modules/pull_and_reboot.sh")
            exit()
        else:
            await ctx.send("Sorry, you can only restart in the bot-testing channel of the memechat server")

    @bot.command()
    async def history(ctx, *args):
        await ctx.send("Reading all messages in this channel (might take a while)...")
        all_msgs = []
        async for msg in ctx.history(limit = None): #reverse = True doesn't reverse message order properly so I have reverse the order myself
            new_bytes = msg.author.display_name.encode() + b': ' + msg.content.encode() #also the reason I'm building a list is because I don't think there's any way to use an async generator as a regular generator (ie, do something like (b'\n'.join(all_msgs) )
            all_msgs.insert(0, new_bytes) #USE insert() TO PREPEND TO LISTS EFFICIENTLY
        pseudo_file = io.BytesIO(b'\n'.join(all_msgs)) #WOULD BE NICE TO JUST DO pseuo_file.write() INSTEAD OF all_msgs.insert BUT MESSAGES HAVE TO BE REVERSED SO THIS IS PROBABLY THE BEST I CAN DO
        message = "Found {} messages".format(len(all_msgs)) #len apparently constant time for lists
        await ctx.send(message, file = discord.File(pseudo_file, filename = "dump.txt"))

    async def play_random_playable():
        playables = storage['playables']
        if len(playables) > 0:
            new_game = discord.Game(name = random.choice(playables))
            await bot.change_presence(activity = new_game)
        else:
            await bot.change_presence(activity = None)

    @bot.command()
    async def unplay(ctx, *, cmd):
        playables = storage['playables']
        if cmd in playables:
            playables.remove(cmd)
            storage.update()
            if ctx.guild is not None and ctx.guild.me.game.name not in playables: #ctx.guild is None if in DMs
                await play_random_playable()
            await ctx.send("removed playable")
        else:
            await ctx.send("Couldn't find playable: " + cmd)

    async def background():
        print('wak background process started')
        while bot.ws is None: #wait until ws connection is made (there is a short period of time after bot.run is called during which the event loop has started but a discord websocket hasn't been established)
            await asyncio.sleep(1)
        while True:
            await play_random_playable()
            await asyncio.sleep(int((random.random()+0.2)*30*60)) #add 0.2 so minimal time isn't 0
    bot.loop.create_task(background())


async def tenor_react(mess, bot):
    if mess.author.id != bot.user.id and random.randint(1, CONFIG['TENOR_CHANCE']) == 1:
        endpoint = "https://api.tenor.com/v1/search?q={search}&key={api_key}&limit=5" #limit search to 5 gifs
        api_key = "CNAW21Y2RSUB"
        msg = mess.content
        msg = re.sub('[.;,!]', '', msg) #remove punctuation from msg (EVEN IF MSG IS 100% PUNCTUATION EVERYTHING WORKS, this is because ''.split(' ') will become [''] which will then search tenor for nothing, which just gets back trending gifs or something so it's fine)
        words = msg.split(' ')
        num_search_terms = len(words)
        if num_search_terms > 3: #max 3 search terms
            num_search_terms = 3
        words.sort(key = len, reverse = True) #sort words from longest to shortest
        for num_words in range(num_search_terms, 0, -1):
            search_words = words[0: num_words]
            search_term = ' '.join(search_words)
            res = requests.get(endpoint.format(search = search_term, api_key = api_key)).json()
            results = res['results']
            if len(results) > 0:
                gif = random.choice(results)
                await mess.channel.send(gif['url'])
                break
            print("no results for '{}'".format(search_term))
