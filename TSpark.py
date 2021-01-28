#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IMPORTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import asyncio
import os
import re
import traceback
import subprocess

import discord
from discord.ext import commands
from tony_modules.storage import JSONStore

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GLOBAL DEFINITIONS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ROOTPATH = os.environ['TONYROOT']  # Bot's root path

MODULES = [
    'tony_modules.lego_funcs',
    'tony_modules.wak_funcs',
    'tony_modules.financial_funcs'
]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOT SETUP
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Pipe(commands.context.Context):
    def __init__(self, ctx):
        self.__ctx = ctx
        self.content = ''

    async def send(self, *args, **kwargs):
        if 'embed' in kwargs:
            if kwargs['embed'].description:
                self.content = kwargs['embed'].description
            elif kwargs['embed'].title:
                self.content = kwargs['embed'].title
        elif args:
            self.content = ' '.join(args)

    def __getattr__(self, attr):
        return getattr(self.__ctx, attr)

    def __setattr__(self, attr, value):
        if attr == '_Pipe__ctx':
            object.__setattr__(self, attr, value)

        return setattr(self.__ctx, attr, value)

class Tony(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = JSONStore(os.path.join(ROOTPATH, 'storage', 'config.json'))  # Auxiliary global variables
    
    async def announce(self, msg, emb = None):
        await bot.get_channel(bot.config['CHANNEL_IDS']['ANNOUNCEMENTS']).send(msg, embed = emb)

    async def log(self, msg, emb = None):
        await bot.get_channel(bot.config['CHANNEL_IDS']['ERROR']).send(msg)
    
    async def mods(self): # Logs module import errors to dedicated error channel
        await bot.wait_until_ready()
        
        for module in MODULES:
            try:
                bot.load_extension(module)
            except Exception as e:
                await bot.log(f"```Failed to import {module}:\n{traceback.format_exc()}```")
        print("Bot up and running")

    def restart(self):
        exit()

    def pull(self):
        return subprocess.run(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def filter(self, msg, bot_allowed = False): # Filter received messages
        return (bot_allowed or msg.author.id != self.user.id) and msg.guild and msg.guild.id == self.config['SERVER_ID'] and msg.channel and msg.channel.id not in self.config['CHANNEL_IDS']['BANNED_CHANNELS']

    async def pipeable(self, command):
        async def wrapper(self, ctx, *args, **kwargs):
            # do before
            await ctx.send("pipe test")
            # do after
        return wrapper

bot = Tony(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# EVENTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@bot.event # Command filtering
async def on_message(msg):
    ctx = await bot.get_context(msg)
    if bot.filter(msg):
        while re.search(r'\$\(![a-z]+[^$()]*\)', msg.content):
            sub = re.search(r'\$\(![a-z]+[^$()]*\)', msg.content)[0]
            args = sub[3:-1].split(" ") # Strip "$(!" and ")" and split the isolated command into pieces
            cmd = args.pop(0) # First piece is the command name
            pipe = Pipe(ctx)
           
            arg_name = str(list(bot.get_command(cmd).clean_params.values())[0])
            if '*' in arg_name:
                await bot.get_command(cmd).__call__(pipe, *args)
            else:
                await bot.get_command(cmd).__call__(pipe, **{arg_name: ' '.join(args)})
            
            msg.content = msg.content.replace(sub, pipe.content, 1)

        await bot.process_commands(msg)  # Process any base commands using the substituted values


@bot.event # Bot error logging
async def on_error(ctx, error):
    await bot.log(f'```{traceback.format_exc()}```')


@bot.event # Command error logging
async def on_command_error(ctx, error):
    suppressed = (commands.CommandNotFound)
    if not isinstance(error, suppressed):
        await ctx.send(f"```{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```")

@bot.event
async def on_guild_channel_create(channel):
    await bot.announce(f"**New channel {channel.mention} has been created**")

@bot.event
async def on_guild_channel_delete(channel):
    await bot.announce(f"**Channel #{channel.name} has been deleted**")

@bot.event
async def on_guild_emojis_update(guild, before, after):
    emb = discord.Embed()
    if (len(before) > len(after)): # Deleted
        emoji = list(set(before) - set(after))[0]
        emb.title = f"Emoji :{emoji.name}: has been deleted" 
    elif (len(before) < len(after)): # Added
        emoji = list(set(after) - set(before))[0]
        emb.title = f"Emoji :{emoji.name}: has been added"
    
    emb.set_image(url=emoji.url)
    await bot.announce('', emb)

@bot.event # Archive deleted messages
async def on_raw_message_delete(raw):
    if raw.cached_message and bot.filter(raw.cached_message):
        msg = raw.cached_message
        channel = bot.get_channel(raw.channel_id)
        emb = discord.Embed(description=msg.content,
                colour=msg.author.colour)  # Create embed
        emb.set_author(name=msg.author.display_name + ':', icon_url=msg.author.avatar_url)
        if msg.attachments:
            emb.set_image(url=list(msg.attachments)[0].url)
        await bot.get_channel(bot.config['CHANNEL_IDS']['RECYCLE_BIN']).send(f"**The following message was deleted from {channel.mention}:**", embed=emb)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@bot.command(description = '~ This command')
async def help(ctx):
    content = '```diff\n<arg>: Mandatory | [arg]: Optional | (arg): Default value | ...: Can provide multiple values\nYou can also pipeline commands using $(<command>), i.e. !speak $(!joke)\n=========='
    for command in bot.commands:
        if command.description is None:
            command.description = ''
        if command.usage is None:
            command.usage = ''

        if len(content) + len(command.name) + len(command.description) + len(command.usage) >= 1900:
            await ctx.send(f"{content}```")
            content = '```diff'
        content += f"\n\n!{command.name} {command.description}{command.usage}"
    await ctx.send(f"{content}```")

@bot.command(description = '~ Restart Tony')
async def restart(ctx):
    await ctx.send("Restarting.... This could take a while")
    bot.restart()

@bot.command(description = '~ Perform a git pull, then restart Tony')
async def rebase(ctx):
    await ctx.send("Pulling and restarting.... This could take a while")
    pull = bot.pull()

    if pull.returncode:
        await ctx.send(f"```Error:\n{pull.stderr.decode('utf-8')}```")
    elif 'up to date' in pull.stdout.decode('utf-8'):
        await ctx.send(f"Nothing changed - not restarting")
    else:
        await ctx.send(f"```{pull.stdout.decode('utf-8')}```")
        bot.restart()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOT STARTUP
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

asyncio.ensure_future(bot.mods())
bot.run(bot.config['API_KEYS']['BOT_TOKEN'], bot=True)

