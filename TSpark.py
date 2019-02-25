#!/usr/local/bin/python3.6
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# IMPORTS

import discord
import traceback
from discord.ext import commands
import os
import json
from tony_modules.wak_funcs import setup as wak_init
from tony_modules.lego_funcs import init as lego_init
import traceback

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# GLOBAL DEFINITIONS

ROOTPATH = os.path.join(os.environ['TONYROOT'])  # Bot's root path
CONFIG = json.load(open(os.path.join(ROOTPATH, 'storage', 'config.json')))  # Auxiliary global variables


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# BOT SETUP

class Tony (commands.Bot):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listeners = {}
        
 
    async def _handle_event(self, event, *args, **kwargs):
        listeners = self._listeners.get(event, [])
        for list in listeners:
            await list(*args, **kwargs)
   
    async def on_message(self, message):
        if message.guild.id == CONFIG['SERVER_ID'] and message.channel.id not in CONFIG['BANNED_CHANNELS']:  # Ignore invalid msgs
            await bot.process_commands(message) #still have to process commands
            await self._handle_event(self.on_message, message)
 
    async def on_reaction_add(self, reaction, user):
        await self._handle_event(self.on_reaction_add, reaction, user)
 
    def event(self, event_type):
        def registrar(listener):
            listeners = self._listeners.get(event_type, [])
            listeners.append(listener)
            self._listeners[event_type] = listeners
        return registrar

 
    async def on_error(self, event, *args, **kwargs):
        await bot.get_channel(548323764186775553).send(f'```{traceback.format_exc()}```')

 
    async def on_ready(self):  # Execute on bot startup
        await bot.wait_until_ready()
        print('Bot up and running')
        
 
    async def help(self, ctx):
        await ctx.send(f"```css\n{CONFIG['HELP_MSG']}```")
        

bot = Tony(command_prefix='!', case_insensitive=False)  # Configure bot prefix
bot.remove_command('help')  # Remove keyword "help" from reserved command list
wak_init(bot)  # Initialize auxiliary functions
lego_init(bot)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

bot.run(CONFIG['TOKEN'])  # Start the bot
