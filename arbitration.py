import discord
from discord.ext import commands, tasks
import requests
import datetime
import sys
import json

sys.path.append('../')
from config import *


bot = commands.Bot(
    command_prefix='!', 
    allowed_mentions=discord.AllowedMentions(everyone=True, roles=True, users=True),
    intents=discord.Intents.default()
    )

mtypes = ['Defense', 'Defection','Disruption', 'Excavation', 'Interception', 'Salvage', 'Survival']
factions = ['Corpus', 'Grineer', 'Infested', 'Orokin']
with open('./solNodes.json') as f:
    solnodes = json.load(f)
CurrentArbi = requests.get('https://10o.io/arbitrations.json').json()[0] ## semlar arbitration data
OldArbi = CurrentArbi

@bot.event
async def on_ready():
    print('<-><-><-><-><-><-><-><-><-><-><->')
    print('<->     Bot Information: ')
    print('<->  Name: {}'.format(bot.user))
    print('<->  ID: {}'.format(bot.user.id))
    print('<-><-><-><-><-><-><-><-><-><-><->')
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='Starting up...', type=3))

@bot.command(name="update")
@commands.is_owner()
async def update(ctx):
    global solnodes
    with open('./solNodes.json') as f:
        solnodes = json.load(f)
    await ctx.send("Updated solnode list.")

def request_arby(): ### get updated arbitration data
    global CurrentArbi
    CurrentArbi = requests.get('https://10o.io/arbitrations.json').json()[0]
    try:
        CurrentArbi['solnodedata']['type'] = solnodes[CurrentArbi['solnode']]['type']
        CurrentArbi['solnodedata']['enemy'] = solnodes[CurrentArbi['solnode']]['enemy']
        CurrentArbi['solnodedata']['node'] = solnodes[CurrentArbi['solnode']]['node']
        CurrentArbi['solnodedata']['planet'] = solnodes[CurrentArbi['solnode']]['planet']
        CurrentArbi['solnodedata']['dark_sector'] = solnodes[CurrentArbi['solnode']]['dark_sector']
        if CurrentArbi['solnodedata']['dark_sector']:
            CurrentArbi['solnodedata']['dark_sector_bonus'] = solnodes[CurrentArbi['solnode']]['dark_sector_bonus']
        CurrentArbi['solnodedata']['tileset'] = solnodes[CurrentArbi['solnode']]['tileset']

    except KeyError:
        print(CurrentArbi)
    if 'bonus' in solnodes[CurrentArbi['solnode']]:
        CurrentArbi['solnodedata']['bonus'] = solnodes[CurrentArbi['solnode']]['bonus']
    return CurrentArbi

@tasks.loop(minutes=1, reconnect=True)
async def arby_post_task():
    global OldArbi
    global CurrentArbi
    CurrentArbi = request_arby()
    prescensetime = datetime.datetime.fromisoformat(CurrentArbi['end'][:-1]) - datetime.datetime.utcnow()
    prescensetime = prescensetime.seconds//60
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name=f"{CurrentArbi['solnodedata']['enemy']} - {CurrentArbi['solnodedata']['type']} on {CurrentArbi['solnodedata']['node']} ~ {prescensetime} minutes remaining.",
            type=3
        )
    )
    if CurrentArbi != OldArbi: ## prevents duplicate posting
        for i in servers:
            try:
                guild = bot.get_guild(i['serverid'])
            except:
                pass
            content = '' # prepares empty string, final string will post with multiple mentions
            # ~~ Factions
            for y in factions:
                if y in CurrentArbi['solnodedata']['enemy']:
                    try:
                        role = discord.utils.get(guild.roles, name=f"{y}")
                        content+=f" {role.mention}"
                    except:
                        pass
            ## ~~ Mission types
            for y in mtypes:
                if y in CurrentArbi['solnodedata']['type']:
                    try:
                        role = discord.utils.get(guild.roles, name=f"{y}")
                        content+=f" {role.mention}"
                    except:
                        pass
                    for f in factions:
                        if f in CurrentArbi['solnodedata']['enemy']:
                            try:
                                role = discord.utils.get(guild.roles, name=f"{f} {y}")
                                content+=f" {role.mention}"
                            except:
                                pass
            # ~~ Dark sector bonus
            x = ''
            if CurrentArbi['solnodedata']['dark_sector'] == True:
                x = f"Dark Sector (+{CurrentArbi['solnodedata']['dark_sector_bonus']['resource']}%)"
            # ~~ Node mentions
            arb = {
                "content": content,
                "username": "Arbitration",
                "avatar_url": "https://cdn.discordapp.com/avatars/705812867781492777/0f0d8efa6759afa9d2bb2618d59dd306.png?size=128",
                "embeds": [{
                        "title": f"{CurrentArbi['solnodedata']['type']} - {CurrentArbi['solnodedata']['enemy']}",
                        "description": f"{CurrentArbi['solnodedata']['node']} ({CurrentArbi['solnodedata']['planet']})\n{x}",
                        "color": 9441039,
                        "thumbnail": {"url": "https://i.imgur.com/2Lyw9yo.png"},
                        "footer": {"text": CurrentArbi['solnodedata']['tileset']}
                        }]
                        }
            try:
                role = discord.utils.get(guild.roles, name=str(CurrentArbi['solnodedata']['node']))
                content+=f' {role.mention}'
                arb['embeds'][0]['color'] = 15844367 # change embed color to gold if role matching node name is found

            except: # if this fails, it means the role wasnt found, therefor its pointless to catch exceptions specifically here
                pass
            try:
                requests.post(i['arbywebhook'], json=arb)
            except Exception as e:
                print(e)
        OldArbi = request_arby() ### setting old arbi to the one that was just posted, so it doesnt send duplicate

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass

bot.run(token, bot=True, reconnect=True)
