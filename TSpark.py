#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# IMPORTS

import discord
import traceback
from discord.ext import commands
import os
import json
from tony_modules.wak_funcs import tenor_reacts as wak_message, setup as wak_init
from tony_modules.lego_funcs import parse_message as lego_message, parse_reaction as lego_reaction, init as lego_init

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# GLOBAL DEFINITIONS

ROOTPATH = os.path.join(os.environ['TONYROOT'])  # Bot's root path
CONFIG = json.load(open(os.path.join(ROOTPATH, 'storage', 'config.json')))  # Auxiliary global variables


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# BOT SETUP

bot = commands.Bot(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list
wak_init(bot)  # Initialize auxiliary functions
lego_init(bot)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# CORE UTILITY


@bot.command()
async def help(ctx):
    await ctx.send(f"```css\n{CONFIG['HELP_MSG']}```")


@bot.event
async def on_message(message):  # Execute on message received
    if message.guild.id == CONFIG['SERVER_ID'] and message.channel.id not in CONFIG['BANNED_CHANNELS']:
        await bot.process_commands(message)  # Process discord-style commands (i.e. !help)
        if message.author.id != bot.user.id:  # If the bot didn't write the message...
            await lego_message(message, bot)  # Apply any post-processing (i.e. triggering based on message content)
            await wak_message(message, bot)


@bot.event
async def on_reaction_add(reaction, user):  # Execute on reaction to message
    await lego_reaction(reaction, user, bot)
    #await wak_reaction(reaction, user, bot)


@bot.event
async def on_error(event, *args, **kwargs):
    await bot.get_channel(548323764186775553).send(f'```{traceback.format_exc()}```')


@bot.event 
async def on_ready():  # Execute on bot startup
    await bot.wait_until_ready()
    print('Bot up and running')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
bot.run(CONFIG['TOKEN'])  # Start the bot
