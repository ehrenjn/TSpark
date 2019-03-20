#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IMPORTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import discord
import traceback
from discord.ext import commands
import os
import json
import traceback
import sys
from tony_modules.util import JSONStore
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GLOBAL DEFINITIONS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


ROOTPATH = os.path.join(os.environ['TONYROOT'])  # Bot's root path
# CONFIG = json.load(open(os.path.join(ROOTPATH, 'storage', 'config.json')))  # Auxiliary global variables
# CONFIG = JSONStore('storage/config.json')
MODULES = ['tony_modules.lego_funcs',
           'tony_modules.wak_funcs']

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOT SETUP
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Tony(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = json.load(open(os.path.join(ROOTPATH, 'storage', 'config.json')))  # Auxiliary global variables


bot = Tony(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list

if __name__ == '__main__':
    for module in MODULES:
        try:
            bot.load_extension(module)
        except Exception as e:
            print(f'Failed to load module {module}.', file=sys.stderr)
            traceback.print_exc()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# EVENTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@bot.event
async def on_message(message):
    if message.guild.id == bot.config['SERVER_ID'] and message.channel.id not in bot.config['BANNED_CHANNELS'] and message.author.id != bot.user.id:
        await bot.process_commands(message)  # still have to process commands


@bot.event
async def on_error(ctx, event, *args, **kwargs):
    await bot.get_channel(548323764186775553).send(f'```{traceback.format_exc()}```')


@bot.event
async def on_ready():  # Execute on bot startup
    await bot.wait_until_ready()
    print('Bot up and running')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@bot.command()
async def help(self):
    await self.send(f"```css\n{bot.config['HELP_MSG']}```")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
bot.run(bot.config['TOKEN'], bot=True)  # Start the bot
