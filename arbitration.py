import discord
from discord.ext import commands
import asyncio
import requests
import json
import time
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys
import os
from discord import Webhook, AsyncWebhookAdapter
import aiohttp

sys.path.append('../')
from config import *


bot = commands.Bot(
    command_prefix='!',
    allowed_mentions=discord.AllowedMentions(everyone=True, roles=True, users=True))

mtypes = ['Defense', 'Defection','Disruption', 'Excavation', 'Interception', 'Salvage', 'Survival']
factions = ['Corpus', 'Grineer', 'Infested', 'Orokin']
solnodes = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/solNodes.json').json() ## personal node export
CurrentArbi = requests.get('https://10o.io/kuvalog.json').json()[0] ## semlar arbitration data
OldArbi = CurrentArbi
sched = AsyncIOScheduler() # needed cause discord.py uses async
sched.start() # starts scheduler for cron task

@bot.event
async def on_ready():
    print('<-><-><-><-><-><-><-><-><-><-><->')
    print('<->     Bot Information: ')
    print('<->  Name: {}'.format(bot.user))
    print('<->  ID: {}'.format(bot.user.id))
    print('<-><-><-><-><-><-><-><-><-><-><->')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='Starting up...', type=3))
    sched.add_job(arby_post_task, trigger='cron', minute='*', second='20', id='Elite', replace_existing=True) # trigger every minute, works best cus cron

@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx, cog):
    extension = cog.title()
    cog = 'cogs.'+str(cog)
    bot.reload_extension(cog)
    cog = bot.get_cog(extension)
    print(cog)
    reload = discord.Embed(title="Cog Reloaded: {}".format(extension),
                           colour=discord.Colour(0x900f0f))
    for x in cog.get_commands():
        reload.add_field(name='{}'.format(x.name), value='  Enabled: {}'.format(x.enabled), inline=True)
    await ctx.send(embed=reload)

@bot.command(name="load")
@commands.is_owner()
async def load(ctx, cog):
    extension = cog.title()
    cog = 'cogs.'+str(cog)
    bot.load_extension(cog)
    cog = bot.get_cog(extension)
    print(cog)
    reload = discord.Embed(title="Cog Loaded: {}".format(extension),
                           colour=discord.Colour(0x900f0f))
    for x in cog.get_commands():
        reload.add_field(name='{}'.format(x.name), value='  Enabled: {}'.format(x.enabled), inline=True)
    await ctx.send(embed=reload)

@bot.command(name="unload")
@commands.is_owner()
async def unload(ctx, cog):
    extension = cog.title()
    cog = 'cogs.'+str(cog)
    bot.unload_extension(cog)
    cog = bot.get_cog(extension)
    print(cog)
    reload = discord.Embed(title="Cog Unloaded: {}".format(extension),
                           colour=discord.Colour(0x900f0f))
    await ctx.send(embed=reload)

def request_arby(): ### get updated arbitration data
    global CurrentArbi
    CurrentArbi = requests.get('https://10o.io/kuvalog.json').json()[0]
    CurrentArbi['solnodedata']['type'] = solnodes[CurrentArbi['solnode']]['type']
    CurrentArbi['solnodedata']['enemy'] = solnodes[CurrentArbi['solnode']]['enemy']
    CurrentArbi['solnodedata']['node'] = solnodes[CurrentArbi['solnode']]['node']
    CurrentArbi['solnodedata']['planet'] = solnodes[CurrentArbi['solnode']]['planet']
    CurrentArbi['solnodedata']['dark_sector'] = solnodes[CurrentArbi['solnode']]['dark_sector']
    CurrentArbi['solnodedata']['tileset'] = solnodes[CurrentArbi['solnode']]['tileset']
    if 'bonus' in solnodes[CurrentArbi['solnode']]:
        CurrentArbi['solnodedata']['bonus'] = solnodes[CurrentArbi['solnode']]['bonus']
    return CurrentArbi

async def arby_post_task():
    global OldArbi
    global CurrentArbi
    CurrentArbi = request_arby()
    prescensetime = datetime.datetime.fromisoformat(CurrentArbi['end'][:-1]) - datetime.datetime.utcnow()
    prescensetime = prescensetime.seconds//60
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=CurrentArbi['solnodedata']['enemy']+' - '+CurrentArbi['solnodedata']['type']+' on '+CurrentArbi['solnodedata']['node']+' ~ '+str(prescensetime)+' minutes remaining.', type=3))
    if request_arby() == OldArbi: ## prevents duplicate posting
        pass
    else:
        guild = bot.get_guild(guildid)
        content = '' # prepares empty string, final string will post with multiple mentions
        # ~~ Factions
        for y in factions:
            if y in CurrentArbi['solnodedata']['enemy']:
                try:
                    role = discord.utils.get(guild.roles, name=str(y))
                    content+=' '+role.mention
                except:
                    pass
        ## ~~ Mission types
        for y in mtypes:
            if y in CurrentArbi['solnodedata']['type']:
                try:
                    role = discord.utils.get(guild.roles, name=str(y))
                    content+=' '+role.mention
                except:
                    pass
                for f in factions:
                    if f in CurrentArbi['solnodedata']['enemy']:
                        try:
                            role = discord.utils.get(guild.roles, name=str(f)+' '+str(y))
                            content+=' '+role.mention
                        except:
                            pass
        # ~~ Dark sector bonus
        x = ''
        if CurrentArbi['solnodedata']['dark_sector'] == True:
            x = 'Dark Sector (+{})'.format(CurrentArbi['solnodedata']['bonus'])
        # ~~ Node mentions
        try:
            role = discord.utils.get(guild.roles, name=str(CurrentArbi['solnodedata']['node']))
            content+=' '+role.mention
            arb = discord.Embed(title=CurrentArbi['solnodedata']['type'] + " - " + CurrentArbi['solnodedata']['enemy'], ### making discord embed here
                                description=CurrentArbi['solnodedata']['node']+' ('+CurrentArbi['solnodedata']['planet']+')\n'+x,
                                colour=discord.Colour(0xf1c40f))
        except:
            arb = discord.Embed(title=CurrentArbi['solnodedata']['type'] + " - " + CurrentArbi['solnodedata']['enemy'], ### making discord embed here
                                description=CurrentArbi['solnodedata']['node']+' ('+CurrentArbi['solnodedata']['planet']+')\n'+x,
                                colour=discord.Colour(0x900f0f))
        arb.set_thumbnail(url='https://i.imgur.com/2Lyw9yo.png')
        arb.set_footer(text=CurrentArbi['solnodedata']['tileset'])
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(arbyhook, adapter=AsyncWebhookAdapter(session))
            await webhook.send(username="Arbitration", avatar_url='https://cdn.discordapp.com/avatars/705812867781492777/0f0d8efa6759afa9d2bb2618d59dd306.png?size=128',content=content, embed=arb) ### sending embed to channel
        OldArbi = request_arby() ### setting old arbi to the one that was just posted, so it doesnt send duplicate

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        pass
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
bot.run(token, bot=True, reconnect=True)
