#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# IMPORTS

import discord
from discord.ext import commands
import os
import json
from tony_modules.wak_funcs import tenor_react, setup as wak_setup
from tony_modules.lego_funcs import parse_message, parse_reaction, init as lego_init

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# GLOBAL DEFINITIONS

ROOTPATH = os.path.join(os.environ['TONYROOT'])  # Bot's root path
VARS = json.load(open(os.path.join(ROOTPATH, 'storage', 'config.json')))  # Auxiliary global variables

for key, value in VARS.items():  # Declares JSON keys as global variables
    if key not in globals():
        globals()[key] = value  # This will make your IDE complain about undeclared variables

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# BOT SETUP

bot = commands.Bot(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list
wak_setup(bot)  # Initialize auxiliary functions
lego_init(bot)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# CORE UTILITY


@bot.command()
async def help(ctx):
    await ctx.send(f"```css\n{HELP_MSG}```")


@bot.event
async def on_message(message):  # Execute on message received
    if message.guild.id == SERVER_ID and message.channel.id not in BANNED_CHANNELS:  # Ignore invalid msgs
        await bot.process_commands(message)  # Process discord-style commands (i.e. !help)
        if message.author.id != bot.user.id:  # If the bot didn't write the message...
            await parse_message(message, bot)  # Apply any post-processing (i.e. triggering based on message content)
            await tenor_react(message, bot)


@bot.event
async def on_reaction_add(reaction, user):  # Execute on reaction to message
    await parse_reaction(reaction, user, bot)


@bot.event 
async def on_ready():  # Execute on bot startup
    await bot.wait_until_ready()
    print('Bot up and running')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
bot.run(TOKEN)  # Start the bot
