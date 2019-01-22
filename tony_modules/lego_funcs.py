import requests
import random
import re
import discord
import asyncio
from .util import \
    JSONStore  # relative import means this wak_funcs.py can only be used as part of the tony_modules package now
import os
import io
from datetime import datetime, timedelta

ROOTPATH = os.path.join(os.environ['TONYROOT'])   #Bot's root path
STORAGE_FILE = os.path.join(ROOTPATH, 'files', 'lego_storage.json')


class LegoStore(JSONStore):
    def __init__(self):
        super().__init__(STORAGE_FILE)
        if self['reminders'] is None:
            self['reminders'] = {}


async def post_parse(message, bot):
    cur_channel = bot.get_channel(message.channel.id)
    if 'ai' in re.findall(r'\bai\b',message.content.lower()):
        async with cur_channel.typing():
            await cur_channel.send('AI...?')
            await asyncio.sleep(random.randint(5, 25))
            await cur_channel.send('Just Sandbox it...\nhttps://www.youtube.com/watch?v=i8r_yShOixM')


async def parsereact(reaction, user, bot):
    emb = discord.Embed(title=reaction.message.content, colour=reaction.message.author.colour)  # Create embed
    emb.set_author(name=reaction.message.author.display_name + ':', icon_url=reaction.message.author.avatar_url)

    try:
        name = reaction.emoji.name
    except AttributeError:
        pass
    else:
        if reaction.message.attachments:  # If the original message has attachments, add them to the embed
            emb.set_image(url=list(reaction.message.attachments)[0].url)

        if name == 'downvote' and reaction.message.author.id != bot.user.id:
            chnl = bot.get_channel(513822540464914432)
            await chnl.send(f"**{user.name} has declared the following to be rude, or otherwise offensive content:**",
                            embed=emb)

        elif name == 'upvote' and reaction.message.author.id != bot.user.id:
            chnl = bot.get_channel(376539985412620289)
            await chnl.send(f"\n\n**{user.name} declared the following to be highly esteemed content:**",
                            embed=emb)


def setup(bot):
    storage = LegoStore()

# AUXILIARY COMMANDS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @bot.command()
    async def joke(ctx):  # Tell a joke using the official Chuck Norris Joke API©
        resp = requests.get('https://api.chucknorris.io/jokes/random').json()  # Get the response in JSON
        emb = discord.Embed(title=resp['value'])  # Prepare the embed
        emb.set_author(name="chuck norris be like...", icon_url=resp['icon_url'].replace('\\', ''))  # Attach icon
        await ctx.send(embed=emb)

    @bot.command()
    async def roll(ctx):  # Outputs the message id of the message sent ("roll")
        await ctx.send(f"{ctx.author.display_name} rolled a {ctx.message.id}")

    @bot.command()
    async def nab(ctx, *cmds):  # Gets all messages between last two instances of messages with given reaction(s)
        #  DEFAULT VALUES
        cmds = list(cmds)
        emojis = []
        num = 1000
        channel = bot.get_channel(ctx.channel.id)
        FLAGS = ['-c', '-n']
        #  FLAG HANDLING
        for cmd in cmds:
            if cmd is '-c':  # Specify the channel to nab from
                channel = bot.get_channel(cmd.pop(cmd.index('-c') + 1))
                continue

            if cmd is '-n':  # Specify number of messages to look through
                num = cmd.pop(cmd.index('-n') + 1)
                if is_num(num):  # If
                    num = is_num(num)
                elif num is 'all':
                    num = 'None'  # None means all messages
                continue

            if cmds[cmds.index(cmd) - 1] not in FLAGS:
                emojis.append(cmd)

        if not emojis:
            await ctx.send('Error: an emoji is required')
            return

        msgs = b''
        num_found = 0
        async for msg in ctx.history(limit=num):
            if all(x in (o.emoji for o in msg.reactions) for x in emojis):
                num_found += 1
            if num_found:
                msgs = msg.author.display_name.encode() + b': ' + msg.content.encode() + b'\n' + msgs
            if num_found is 2:
                break
        else:
            await channel.send(f'Error: Two instances of {emojis} not found in last {num} messages')
            return

        await channel.send(file=discord.File(io.BytesIO(msgs), filename='nab.txt'))

    @bot.command()
    async def search(ctx, *cmd):
        cmd = list(cmd)
        users = []
        reactions = []
        channels = []
        msgs = []
        num = 1000
        while any(x in cmd for x in ['-u', '-n', '-r', '-c']):
            if '-u' in cmd:
                user = cmd.pop(cmd.index('-u') + 1)
                if user.lower() == 'all':
                    users = ctx.guild.members
                else:
                    users.append(bot.get_user(int(re.sub('[<@>]', '', user))))
                cmd.remove('-u')

            if '-r' in cmd:
                reactions.append(cmd.pop(cmd.index('-r') + 1))
                cmd.remove('-r')

            if '-c' in cmd:
                chan = cmd.pop(cmd.index('-c') + 1)
                if chan.lower() == 'all':
                    channels = ctx.guild.text_channels
                else:
                    channels.append(bot.get_channel(int(re.sub('[<#>]', '', chan))))
                cmd.remove('-c')

            if '-n' in cmd:
                num = cmd.pop(cmd.index('-n') + 1)
                if num.lower() == 'all':
                    num = None
                elif is_num(num):
                    num = is_num(num)
                else:
                    await ctx.send('Error: Num value must be "all" or int')
                    return
                cmd.remove('-n')

        if not channels:
            channels.append(ctx.channel)
        if not users:
            users.append(ctx.author)
        print(users)
        print(channels)
        print(reactions)
        await ctx.send(f"```Searching through last {num} messages, in channel(s) {', '.join(x.name for x in channels)} by user(s) {'/'.join(x.display_name for x in users)} with reaction(s) '{'/'.join(reactions)}' for string(s) '{'/'.join(cmd)}'```")
        for channel in ctx.guild.text_channels:
            if channel.id in (x.id for x in channels):
                try:
                    async for msg in channel.history(limit=num):
                        if msg.author.id not in (o.id for o in users):
                            continue
                        if reactions and not set(reactions).intersection((o.emoji for o in msg.reactions)):
                            continue
                        if not cmd or any(x.lower() in msg.content.lower() for x in cmd):
                            msgs.insert(0, f"{msg.author.display_name} ({str(msg.created_at.replace(microsecond=0) - timedelta(hours=5))}): {msg.content}")
                except discord.Forbidden:
                    pass
                msgs.insert(0, f"~~~~ {channel.name.upper()} ~~~~")
        try:
            await ctx.send(content=f"{len(msgs) - len(channels)} messages found.", file=discord.File(io.BytesIO('\n'.join(msgs).encode()), filename=f"{str(ctx.message.created_at.replace(microsecond=0) - timedelta(hours=5))}-dump.txt'"))
        except discord.HTTPException:
            await ctx.send('Error: Dump file too large')

    @bot.command()
    async def moji(ctx, opts = '-l', name = '', link = ''):
        mojis = storage['mojis']
        if opts == '-l':
            await ctx.send('```Available mojis:\n' + '\n'.join(storage['mojis']) + '```')

        elif opts == '-a':
            mojis[name] = link
            storage.update()
            await ctx.send(f"Moji {name} successfully added")

        elif opts == '-r':
            del mojis[name]
            storage.update()
            await ctx.send(f"Moji {name} successfully removed")

        elif opts in mojis:
            await ctx.send(mojis[opts])

        else:
            await ctx.send(f"Moji '{opts}' not found")
        await ctx.message.delete()

    @bot.command()
    async def reminder(ctx, *cmd):
        cmd = list(cmd)
        rem_index = 1
        rem_date = datetime.now().replace(second=0, microsecond=0)
        if '-l' in cmd:
            printlist = 'Reminders:\n'
            for x in storage['reminders']:
                printlist += f"{x}:\n"
                for y in storage['reminders'][x]:
                    printlist += f"\t{y} : {str(storage['reminders'][x][y])}\n"
            await ctx.send(f"```{printlist}```")
            return
        if '-u' in cmd:
            rem_user = cmd.pop(cmd.index('-u') + 1)
            cmd.remove('-u')
        else:
            rem_user = ctx.author.mention
        if 'days' or 'hours' or 'minutes' in cmd:
            try:
                rem_date += timedelta(days=is_num(cmd.pop(cmd.index('days') - 1)))
                cmd.remove('days')
            except ValueError:
                pass
            try:
                rem_date += timedelta(hours=is_num(cmd.pop(cmd.index('hours') - 1)))
                cmd.remove('hours')
            except ValueError:
                pass
            try:
                rem_date += timedelta(minutes=is_num(cmd.pop(cmd.index('minutes') - 1)))
                cmd.remove('minutes')
            except ValueError:
                pass
        else:
            await ctx.send('Error: Must include time formatting')

        for x in storage['reminders']:
            if int(x) + 1 not in storage['reminders']:
                rem_index = int(x) + 1
                break

        storage['reminders'][rem_index] = {}
        storage['reminders'][rem_index]['user'] = rem_user
        storage['reminders'][rem_index]['date'] = str(rem_date)
        storage['reminders'][rem_index]['reminder'] = ' '.join(cmd)
        storage['reminders'][rem_index]['channel'] = ctx.message.channel.id
        storage.update()
        await ctx.send(f"Reminder '{' '.join(cmd)}' added for {rem_date}")

    @bot.command()
    async def discloud(ctx, *cmd):
        cmd = list(cmd)
        path = os.path.join(ROOTPATH, 'files', 'discloud')
        if '-l' in cmd:
            liststring = ""
            for num, val in enumerate(os.listdir(path)):
                liststring += f"{num + 1} - {val}\n"
            await ctx.send(f"```{liststring}```")
            return

        if '-s' in cmd:
            cmd.remove('-s')
            msgs = []
            if not cmd:
                msgs.append(ctx.message)
            else:
                for mID in cmd:
                    msgs.append(await ctx.get_message(mID))
            for msg in msgs:
                for attachment in msg.attachments:
                    await attachment.save(os.path.join(path, attachment.filename))
                    await ctx.send(f'File "{attachment.filename}" stored')

        if '-g' in cmd:
            cmd.remove('-g')
            if not cmd:
                await ctx.send('Please specify file(s) by index (i.e. "1 2 4 5")')
            else:
                files = []
                for data in cmd:
                    data = is_num(data) - 1
                    files.append(discord.File(open(os.path.join(path, os.listdir(path)[data]), 'rb'), filename=os.listdir(path)[data]))
                try:
                    message = await ctx.send(content='```Warning, file(s) will be deleted in 5 minutes.```', files=files)
                    await asyncio.sleep(300)
                    await message.delete()
                except IndexError:
                    await ctx.send('Error: Index not found')

    async def check_reminder():
        reminders = storage['reminders']
        for x in list(reminders):
            if str(datetime.now().replace(second=0, microsecond=0)) >= reminders[x]['date']:
                await bot.get_channel(reminders[x]['channel']).send(reminders[x]['user'] + ' - ' + reminders[x]['reminder'])
                del reminders[x]
                storage.update()

    def is_num(s):
        try:
            int(s)
        except ValueError:
            return False
        finally:
            return int(s)

    async def lego_background():
        print('lego background process started')
        while bot.ws is None:
            await asyncio.sleep(1)
        while True:
            await check_reminder()
            await asyncio.sleep(15)

    bot.loop.create_task(lego_background())
