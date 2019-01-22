#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# IMPORTS
from discord.ext import commands
import os
from tony_modules.wak_funcs import setup as wak_setup
from tony_modules.lego_funcs import setup as lego_setup, post_parse, parsereact
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# GLOBAL DEFINITIONS
ROOTPATH = os.path.join(os.environ['TONYROOT'])   #Bot's root path
TOKEN = open(os.path.join(ROOTPATH, 'token'), 'r').read()  # Read token from local file (as opposed to HCing)
BANNED_CHANNELS = [channel.rstrip('\n') for channel in open('files/blacklist')]  # Read list of banned channels
COMMANDS = open(os.path.join(ROOTPATH, 'files', 'commands'), 'r').read()  # Read help message
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# BOT SETUP
bot = commands.Bot(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list
wak_setup(bot)  # Initialize auxiliary functions
lego_setup(bot)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# CORE UTILITY


@bot.command()
async def help(ctx):
    await ctx.send(f"```css\n{COMMANDS}```")


@bot.event
async def on_message(message):  # Execute on message received
    if message.guild.id == 338145800620212234 and message.channel.id not in BANNED_CHANNELS: # Ignore invalid msgs
        await bot.process_commands(message)
        if message.author.id != bot.user.id:
            await post_parse(message, bot)

@bot.event
async def on_reaction_add(reaction, user):  # Execute on reaction to message
    await parsereact(reaction, user, bot)

@bot.event 
async def on_ready():  # Execute on bot startup
    await bot.wait_until_ready()
    print('Bot up and running')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
bot.run(TOKEN)  # Start the bot
