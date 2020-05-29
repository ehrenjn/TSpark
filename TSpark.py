#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IMPORTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import asyncio
import os
import re
import traceback

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

class Tony(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = JSONStore(os.path.join(ROOTPATH, 'storage', 'config.json'))  # Auxiliary global variables
    
    async def announce(self, msg, emb = None):
        await bot.get_channel(bot.config['ANNOUNCEMENTS']).send(msg, embed = emb)

    async def log(self, msg, emb = None):
        await bot.get_channel(bot.config['ERROR']).send(msg)
    
    async def mods(self): # Logs module import errors to dedicated error channel
        await bot.wait_until_ready()
        
        for module in MODULES:
            try:
                bot.load_extension(module)
            except Exception as e:
                await bot.log(f"```Failed to import {module}:\n{traceback.format_exc()}```")
        print("Bot up and running")

    def filter(self, msg, bot_allowed = False): # Filter received messages
        return (bot_allowed or msg.author.id != self.user.id) and msg.guild.id == self.config['SERVER_ID'] and msg.channel.id not in self.config['BANNED_CHANNELS']

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
            msg.content = msg.content.replace(sub, await bot.get_command(cmd).__call__(ctx, *args, pipe=True), 1)

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
        await bot.get_channel(bot.config['RECYCLE_BIN']).send(f"**The following message was deleted from {channel.mention}:**", embed=emb)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@bot.command()
async def help(ctx):
    await ctx.send(f"```css\n{open(os.path.join(ROOTPATH, 'help.txt'), 'r').read()}```")


@bot.command()
async def restart(ctx):
    await ctx.send("Restarting.... This could take a while")
    exit()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOT STARTUP
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

asyncio.ensure_future(bot.mods())
bot.run(bot.config['TOKEN'], bot=True)

