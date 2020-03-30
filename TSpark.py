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
    
    async def mods(self): # Logs module import errors to dedicated error channel
        await bot.wait_until_ready()
        
        for module in MODULES:
            try:
                bot.load_extension(module)
            except Exception as e:
                await bot.get_channel(548323764186775553).send(
                        f"```Failed to import {module}:\n{traceback.format_exc()}```")
        print("Bot up and running")

bot = Tony(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# EVENTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@bot.event
async def on_message(msg):
    ctx = await bot.get_context(msg)
    if msg.guild.id == bot.config['SERVER_ID'] and msg.channel.id not in bot.config['BANNED_CHANNELS']:
        while re.search(r'\$\(![a-z]+[^$()]*\)', msg.content):
            sub = re.search(r'\$\(![a-z]+[^$()]*\)', msg.content)[0]
            args = sub[3:-1].split(" ") # Strip "$(!" and ")" and split the isolated command into pieces
            cmd = args.pop(0) # First piece is the command name
            msg.content = msg.content.replace(sub, await bot.get_command(cmd).__call__(ctx, *args, pipe=True), 1)

        await bot.process_commands(msg)  # Process any base commands using the substituted values


@bot.event
async def on_error(ctx, error): # Send any bot errors to dedicated error log channel
    await bot.get_channel(548323764186775553).send(f'```{traceback.format_exc()}```')


@bot.event
async def on_command_error(ctx, error): # Send any command errors to the current channel
    suppressed = (commands.CommandNotFound)
    if not isinstance(error, suppressed):
        await ctx.send(f"```{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```")

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

