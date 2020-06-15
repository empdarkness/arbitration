import discord
from discord.ext import commands
import asyncio
import requests
import string
import json
import prettytable
import datetime
import time
import sys
from discord import Webhook, AsyncWebhookAdapter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import re


sys.path.append('../')
from config import *


bot = commands.Bot(command_prefix='!',
                   description='A Warframe based module.')
CurrentArbi = requests.get('https://10o.io/kuvalog.json').json()[0] ## semlar arbitration data
solNodes = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/solNodes.json').json() ## personal node export
missionTypes = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/missionTypes.json').json()
sortieData = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/sortieData.json').json()
lang = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/languages.json').json()
sched = AsyncIOScheduler() # needed cause discord.py uses async
sched.start() # starts scheduler for cron task
gftla = []
gftlb = []
af    = []
bf    = []
inva  = []
invb  = []
redtext = []
OldBaro = ""
invasionitem = ['Orokin Reactor', 'Orokin Catalyst']


class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='price', description='warframe.market price checker', brief='warframe.market price checker', usage='<item>')
    async def price(self, ctx, *args):
            mesg = ' '.join(args)
            search = mesg.lower()
            if 'melee' == search:
                search = 'melee riven mod (veiled)'
            elif 'melee riven' in search:
                search = 'melee riven mod (veiled)'
            elif 'rifle' == search:
                search = 'rifle riven mod (veiled)'
            elif 'rifle riven' in search:
                search = 'rifle riven mod (veiled)'
            elif 'shotgun' == search:
                search = 'shotgun riven mod (veiled)'
            elif 'shotgun riven' in search:
                search = 'shotgun riven mod (veiled)'
            elif 'zaw' == search:
                search = 'zaw riven mod (veiled)'
            elif 'zaw riven' in search:
                search = 'zaw riven mod (veiled)'
            elif 'kitgun' == search:
                search = 'kitgun riven mod (veiled)'
            elif 'kitgun riven' in search:
                search = 'kitgun riven mod (veiled)'
            elif 'companion riven' in search:
                search = 'companion rifle riven mod (veiled)'
            item = requests.get('https://api.warframe.market/v1/items/' + search.replace(' ', '_') + '/statistics').json()
            image = requests.get('https://api.warframe.market/v1/items/' + search.replace(' ', '_')).json()
            item = item['payload']['statistics_closed']['48hours'][-1]['min_price']
            embed = discord.Embed(title='Click for orders',
                                  colour=discord.Colour(0x9013fe),
                                  url='https://warframe.market/items/' + search.replace(' ', '_'),
                                  description=str(int(item))+' Platinum')
            embed.set_thumbnail(url='https://warframe.market/static/assets/' + image['payload']['item']['items_in_set'][-1]['icon'])
            embed.set_footer(text='Data retrieved from warframe.market', icon_url='https://warframe.market/favicon.png')
            await ctx.send(embed=embed)

    @price.error
    async def priceerror(self, ctx, error):
        embed = discord.Embed(title='Syntax Error',
                              colour=discord.Colour(0x9013fe),
                              description='Did you mistype the item name?')
        await ctx.send(embed=embed)

    @commands.command(name="specter", description='Specter Scaling Calculator', brief='Specter Scaling Calculator', usage='<Warframe> <Weapon Name or TotalDMG> <CurrentLevel> <MissionLevel>')
    async def specter(self, ctx, specter, damage, CurrentLevel, MissionLevel, *args):
        damage = damage.title()
        specter = specter.title()
        primary = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Primary.json').json()
        secondary = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Secondary.json').json()
        melee = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Melee.json').json()
        if damage.isdigit() == False:
            for i in primary:
                if damage == i['name']:
                    damage = int(i['totalDamage'])*int(i['multishot'])
                    fireRate = float(i['fireRate'])
            for i in secondary:
                if damage == i['name']:
                    damage = int(i['totalDamage'])*int(i['multishot'])
                    fireRate = float(i['fireRate'])
            for i in melee:
                if damage == i['name']:
                    damage = int(i['totalDamage'])
                    fireRate = float(i['fireRate'])
        warframes = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Warframes.json').json()
        try:
            MissionLevel = MissionLevel.split('-')
            MissionLevel = ((int(MissionLevel[0])+int(MissionLevel[1]))/2)
        except:
            MissionLevel = MissionLevel[0]
        LevelDiff = float(CurrentLevel) - float(MissionLevel)
        multi = 1+0.015*(float(LevelDiff))**1.55
        damage = float(multi)*float(damage)*float(fireRate)
        for i in warframes:
            if specter in i['name']:
                if 'old' in args:
                    HealthMulti = (1 + float(LevelDiff)**1.75 * 0.005)
                    ShieldMulti = (1 + float(LevelDiff)**2 * 0.0075)
                    ArmorMulti  = (1 + float(LevelDiff)**1.75 * 0.005)
                    HealthValueOld = int(i['health']) * HealthMulti
                    ShieldValueOld = int(i['shield']) * ShieldMulti
                    ArmorValueOld = int(i['armor']) * ArmorMulti
                    CurrentShieldValue = ShieldValueOld
                    CurrentHealthValue = HealthValueOld
                    CurrentArmorValue = ArmorValueOld
                    if not i['shield'] == 0 and i['armor'] == 0:
                        ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                        DamageReduction = 0
                    elif i['shield'] == 0 and not i['armor'] == 0:
                        ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                        DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                    elif not i['shield'] == 0 and not i['armor'] == 0:
                        ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                        DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                    DamageReduction = round(DamageReduction, 5)
                    embed = discord.Embed(title=i['name'],
                                          description='**DPS:** {:,}'.format(int(damage))+'\n**Health:** {:,}'.format(int(CurrentHealthValue))+'\n**Armor:** {:,}'.format(int(CurrentArmorValue))+'\n**Shields:** {:,}'.format(int(CurrentShieldValue))+'\n**DR:** {}%'.format(DamageReduction)+'\n**EHP:** {:,}'.format(int(ehp)),
                                          colour=discord.Colour(0x7ed321))
                    embed.set_thumbnail(url='https://raw.githubusercontent.com/empdarkness/warframe-data/master/img/'+i['imageName'])
                    embed.set_footer(text='This does not take into account damage types.')
                    await ctx.send(embed=embed)
                else:
                    HealthMultiLow = (1 + float(LevelDiff)**2 * 0.015)
                    ShieldMultiLow = (1 + float(LevelDiff)**1.75 * 0.02)
                    ArmorMultiLow  = (1 + float(LevelDiff)**1.75 * 0.005)
                    HealthMultiHigh = (1 + float(LevelDiff)**0.5 * 10.7331)
                    ShieldMultiHigh = (1 + float(LevelDiff)**0.75 * 1.6)
                    ArmorMultiHigh = (1 + float(LevelDiff)**0.75 * 0.4)
                    HealthValueLow = int(i['health']) * HealthMultiLow
                    ShieldValueLow = int(i['shield']) * ShieldMultiLow
                    ArmorValueLow = int(i['armor']) * ArmorMultiLow
                    HealthValueHigh = int(i['health']) * HealthMultiHigh
                    ShieldValueHigh = int(i['shield']) * ShieldMultiHigh
                    ArmorValueHigh = int(i['armor']) * ArmorMultiHigh
                    if int(LevelDiff) <=70:
                        HealthMulti = HealthMultiLow
                        ShieldMulti = ShieldMultiLow
                        ArmorMulti = ArmorMultiLow
                        CurrentShieldValue = ShieldValueLow
                        CurrentHealthValue = HealthValueLow
                        CurrentArmorValue = ArmorValueLow
                        if not i['shield'] == 0 and i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                            DamageReduction = 0
                        elif i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        elif not i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        DamageReduction = round(DamageReduction, 5)
                    if int(LevelDiff) >=80:
                        HealthMulti = HealthMultiHigh
                        ShieldMulti = ShieldMultiHigh
                        ArmorMulti = ArmorMultiHigh
                        CurrentShieldValue = ShieldValueHigh
                        CurrentHealthValue = HealthValueHigh
                        CurrentArmorValue = ArmorValueHigh
                        DamageReduction = 0
                        ehp = CurrentHealthValue
                        if not i['shield'] == 0 and i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                            DamageReduction = 0
                        elif i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        elif not i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        DamageReduction = round(DamageReduction, 5)
                    if 70 <= LevelDiff <=80:
                        x = (LevelDiff - 70)/ (80-70)
                        s = (3*(x)**2) - (2*(x)**3)
                        HealthMulti = ShieldValueLow+s*ShieldValueHigh
                        ShieldMulti = HealthValueLow+s*HealthValueHigh
                        ArmorMulti = ArmorValueLow+s*ArmorValueHigh
                        CurrentShieldValue = (1-s)*ShieldValueLow+s*ShieldValueHigh
                        CurrentHealthValue = (1-s)*HealthValueLow+s*HealthValueHigh
                        CurrentArmorValue = (1-s)*ArmorValueLow+s*ArmorValueHigh
                        if not i['shield'] == 0 and i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                            DamageReduction = 0
                        elif i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        elif not i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        DamageReduction = round(DamageReduction, 5)
                    embed = discord.Embed(title=i['name'],
                                          description='**DPS:** {:,}'.format(int(damage))+'\n**Health:** {:,}'.format(int(CurrentHealthValue))+'\n**Armor:** {:,}'.format(int(CurrentArmorValue))+'\n**Shields:** {:,}'.format(int(CurrentShieldValue))+'\n**DR:** {}%'.format(DamageReduction)+'\n**EHP:** {:,}'.format(int(ehp)),
                                          colour=discord.Colour(0x7ed321))
                    embed.set_thumbnail(url='https://raw.githubusercontent.com/empdarkness/warframe-data/master/img/'+i['imageName'])
                    embed.set_footer(text='This does not take into account damage types.')
                    await ctx.send(embed=embed)

    @specter.error
    async def spectererror(self, ctx, error):
        embed = discord.Embed(title='Syntax Error',
                             description='!specter <Warframe> <Base Dmg / Weapon> <CurrentLevel> <MissionLevel>\nUse `""` to use weapons with multiple words.\nUse the base mission level. Ex. Mot = 40\n`!specter Nidus "Prisma Gorgon" 1000 40`',
                             colour=discord.Colour(0x900f0f))
        await ctx.send(embed=embed)

    @commands.command(name="enemy")
    async def enemy(self, ctx, enemy, damage, CurrentLevel, MissionLevel, *args):
        old = ''.join(args)
        damage = damage.title()
        enemyx = enemy.title()
        fireRate = ''
        primary = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Primary.json').json()
        secondary = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Secondary.json').json()
        melee = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Melee.json').json()
        enemy = requests.get('https://raw.githubusercontent.com/empdarkness/warframe-data/master/Enemy.json').json()
        try:
            if damage == 'Primary':
                for i in enemy:
                    if enemyx == i['name']:
                        weapon = i['primary']
                        for x in primary:
                            if weapon == x['name']:
                                damage = int(x['totalDamage'])*int(x['multishot'])
                                fireRate = float(x['fireRate'])
                                for i in enemy:
                                    if enemyx == i['name']:
                                        weapon = i['primary']
                                        for x in secondary:
                                            if weapon == x['name']:
                                                damage = int(x['totalDamage'])*int(x['multishot'])
                                                fireRate = float(x['fireRate'])
            if damage == 'Melee':
                for i in enemy:
                    if enemyx == i['name']:
                        weapon = i['melee']
                        for x in melee:
                            if weapon == x['name']:
                                damage = int(x['totalDamage'])
                                fireRate = float(x['fireRate'])
        except:
            damage = 0
        LevelDiff = float(CurrentLevel) - float(MissionLevel)
        multi = 1+0.015*(float(LevelDiff))**1.55
        if fireRate == True:
            damage = float(multi)*float(damage)*float(fireRate)
        else:
            damage = float(multi)*float(damage)
        count=0
        for i in enemy:
            if enemyx == i['name']:
                if count == 0:
                    if 'old' in old:
                        count+=1
                        HealthMulti = (1 + float(LevelDiff)**1.75 * 0.005)
                        ShieldMulti = (1 + float(LevelDiff)**2 * 0.0075)
                        ArmorMulti  = (1 + float(LevelDiff)**1.75 * 0.005)
                        HealthValueOld = int(i['health']) * HealthMulti
                        ShieldValueOld = int(i['shield']) * ShieldMulti
                        ArmorValueOld = int(i['armor']) * ArmorMulti
                        CurrentShieldValue = ShieldValueOld
                        CurrentHealthValue = HealthValueOld
                        CurrentArmorValue = ArmorValueOld
                        if not i['shield'] == 0 and i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                            DamageReduction = 0
                        elif i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        elif not i['shield'] == 0 and not i['armor'] == 0:
                            ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                            DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                        DamageReduction = round(DamageReduction, 5)
                        embed = discord.Embed(title=i['name'],
                                              description='**DPS:** {:,}'.format(int(damage))+'\n**Health:** {:,}'.format(int(CurrentHealthValue))+'\n**Armor:** {:,}'.format(int(CurrentArmorValue))+'\n**Shields:** {:,}'.format(int(CurrentShieldValue))+'\n**DR:** {}%'.format(DamageReduction)+'\n**EHP:** {:,}'.format(int(ehp)),
                                              colour=discord.Colour(0x7ed321))
                        embed.set_footer(text='This does not take into account damage types.')
                        await ctx.send(embed=embed)
                    else:
                        count+=1
                        HealthMultiLow = (1 + float(LevelDiff)**2 * 0.015)
                        ShieldMultiLow = (1 + float(LevelDiff)**1.75 * 0.02)
                        ArmorMultiLow  = (1 + float(LevelDiff)**1.75 * 0.005)
                        HealthMultiHigh = (1 + float(LevelDiff)**0.5 * 10.7331)
                        ShieldMultiHigh = (1 + float(LevelDiff)**0.75 * 1.6)
                        ArmorMultiHigh = (1 + float(LevelDiff)**0.75 * 0.4)
                        HealthValueLow = int(i['health']) * HealthMultiLow
                        ShieldValueLow = int(i['shield']) * ShieldMultiLow
                        ArmorValueLow = int(i['armor']) * ArmorMultiLow
                        HealthValueHigh = int(i['health']) * HealthMultiHigh
                        ShieldValueHigh = int(i['shield']) * ShieldMultiHigh
                        ArmorValueHigh = int(i['armor']) * ArmorMultiHigh
                        if int(LevelDiff) <=70:
                            HealthMulti = HealthMultiLow
                            ShieldMulti = ShieldMultiLow
                            ArmorMulti = ArmorMultiLow
                            CurrentShieldValue = ShieldValueLow
                            CurrentHealthValue = HealthValueLow
                            CurrentArmorValue = ArmorValueLow
                            if not i['shield'] == 0 and i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                                DamageReduction = 0
                            elif i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            elif not i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            DamageReduction = round(DamageReduction, 5)
                        if int(LevelDiff) >=80:
                            HealthMulti = HealthMultiHigh
                            ShieldMulti = ShieldMultiHigh
                            ArmorMulti = ArmorMultiHigh
                            CurrentShieldValue = ShieldValueHigh
                            CurrentHealthValue = HealthValueHigh
                            CurrentArmorValue = ArmorValueHigh
                            DamageReduction = 0
                            ehp = CurrentHealthValue
                            if not i['shield'] == 0 and i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                                DamageReduction = 0
                            elif i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            elif not i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            DamageReduction = round(DamageReduction, 5)
                        if 70 <= LevelDiff <=80:
                            x = (LevelDiff - 70)/ (80-70)
                            s = (3*(x)**2) - (2*(x)**3)
                            HealthMulti = ShieldValueLow+s*ShieldValueHigh
                            ShieldMulti = HealthValueLow+s*HealthValueHigh
                            ArmorMulti = ArmorValueLow+s*ArmorValueHigh
                            CurrentShieldValue = (1-s)*ShieldValueLow+s*ShieldValueHigh
                            CurrentHealthValue = (1-s)*HealthValueLow+s*HealthValueHigh
                            CurrentArmorValue = (1-s)*ArmorValueLow+s*ArmorValueHigh
                            if not i['shield'] == 0 and i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti + ShieldMulti*(i['shield']/i['health']))
                                DamageReduction = 0
                            elif i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300)))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            elif not i['shield'] == 0 and not i['armor'] == 0:
                                ehp = i['health'] * (HealthMulti*(1+((i['armor']*ArmorMulti)/300))+ShieldMulti*((i['shield'])/(i['health'])))
                                DamageReduction = round(((CurrentArmorValue)/(CurrentArmorValue+300)), 5)*100
                            DamageReduction = round(DamageReduction, 5)
                        embed = discord.Embed(title=i['name'],
                                              description='**DPS:** {:,}'.format(int(damage))+'\n**Health:** {:,}'.format(int(CurrentHealthValue))+'\n**Armor:** {:,}'.format(int(CurrentArmorValue))+'\n**Shields:** {:,}'.format(int(CurrentShieldValue))+'\n**DR:** {}%'.format(DamageReduction)+'\n**EHP:** {:,}'.format(int(ehp)),
                                              colour=discord.Colour(0x7ed321))
                        embed.set_footer(text='This does not take into account damage types.')
                        await ctx.send(embed=embed)

    @enemy.error
    async def enemyerror(self, ctx, error):
        print(error)
        embed = discord.Embed(title='Syntax Error',
                             description='!enemy "Enemy" <primary/melee> <CurrentLevel> <Mission Level>\n`Primary` = Normal weapon\n`Melee` = Disarmed\nUse the base mission level. Ex. Mot = 40\nSome enemies may not have known weapon references and will show 0 damage.\n!enemy "Corrupted Heavy Gunner" primary 1000 40',
                             colour=discord.Colour(0x900f0f))
        await ctx.send(embed=embed)


    # ehp calculator
    @commands.command(name="ehp")
    async def ehp(self, ctx, health, armor):
            calc = int(health)*(1 + int(armor)/300)
            ehpe = discord.Embed(title="Effective Health Calculation",
                                 description="**Armor:** *" + str(armor) + "*\n**Health:** *" + str(health) + "* \n**Effective Health:** *" + str(int(calc)) + "*",
                                 colour=discord.Colour(0x900f0f))
            ehpe.set_footer(text="This does not take into account damage types.")
            await ctx.send(embed=ehpe)

    @ehp.error
    async def ehperror(self, ctx, error):
        await ctx.send("Invalid syntax.\n!ehp <total health> <total armor> <total shields>")

    # status calculator
    @commands.command(name="status")
    async def status(self, ctx, base, status):
        bs = int(base)
        st = float(status)
        calc = bs + (bs * (float(st)/100))
        await ctx.send(calc)

    @status.error
    async def statuserror(self, ctx, error):
        await ctx.send("Invalid Syntax.\n!status <base status> <status to add>")

    @bot.command(name='nightwave', aliases=['nw'])
    async def nw(self, ctx):
        nwapi = requests.get('http://content.warframe.com/dynamic/worldState.php').json()['SeasonInfo']
        timestamp = datetime.datetime.fromtimestamp(int(nwapi['Expiry']['$date']['$numberLong'])/1000)
        nightwave = discord.Embed(title="Nightwave",
                                  colour=discord.Colour(0x900f0f),
                                  timestamp=timestamp)
        nightwave.set_footer(text='Season '+str(nwapi['Season'])+' - Phase '+str(nwapi['Phase'])+' ends')
        for i in nwapi['ActiveChallenges']:
            nightwave.add_field(name=lang[i['Challenge'].lower()]['value']+' - **'+str(lang[i['Challenge'].lower()]['standing'])+'**', value=lang[i['Challenge'].lower()]['desc'], inline=True)
        await ctx.send(embed=nightwave)

    @nw.error
    async def nwerror(self, ctx, error):
        await ctx.send(content=error)

    # void trader
    @bot.command(name="baro")
    async def baro(self, ctx):
        voidTrader = request_baro()
        if voidTrader['active'] == True:
            x = prettytable.PrettyTable(["Item", "Ducats", "Credits"])
            x.sortby = "Ducats"
            x.reversesort=True
            for item in voidTrader['inventory']:
                x.add_row((item["item"], item["ducats"], item["credits"]))
            await ctx.send(str("```") + str(x) + ("```"))
        else:
            timestamp = datetime.datetime.fromtimestamp(voidTrader['activation'])
            baro = discord.Embed(title="Baro Ki'Teer is currently not available.",
                                 colour=discord.Colour(0x900f0f),
                                 timestamp=timestamp)
            baro.set_footer(text="Arrives at "+voidTrader['location'])
            await ctx.send(embed=baro)

    @baro.error
    async def baroerror(self, ctx, error):
        await ctx.send(error)

    # sortie
    @bot.command(name="sortie")
    async def sortie(self, ctx):
        sortie = request_sortie()
        timestamp = (datetime.datetime.fromtimestamp(int(sortie['expiry'])/1000))
        arb = discord.Embed(title=sortie['boss'],
                            colour=discord.Colour(0x900f0f),
                            timestamp=timestamp)
        arb.add_field(name=sortie['missions'][0]['node']['node']+' ({})'.format(sortie['missions'][0]['node']['planet'])+' - '+sortie['missions'][0]['missionType'], value=sortie['missions'][0]['modifierType']+':\n - '+sortie['missions'][0]['modifierDescription'], inline=False)
        arb.add_field(name=sortie['missions'][1]['node']['node']+' ({})'.format(sortie['missions'][1]['node']['planet'])+' - '+sortie['missions'][1]['missionType'], value=sortie['missions'][1]['modifierType']+':\n - '+sortie['missions'][1]['modifierDescription'], inline=False)
        arb.add_field(name=sortie['missions'][2]['node']['node']+' ({})'.format(sortie['missions'][2]['node']['planet'])+' - '+sortie['missions'][2]['missionType'], value=sortie['missions'][2]['modifierType']+':\n - '+sortie['missions'][2]['modifierDescription'], inline=False)
        arb.set_footer(text="Expires")
        arb.set_thumbnail(url='https://i.imgur.com/7Avse3e.png')
        await ctx.send(embed=arb)

    @sortie.error
    async def sortieerror(self, ctx, error):
        await ctx.send(error)

def request_sortie():
    sortie = requests.get('http://content.warframe.com/dynamic/worldState.php').json()['Sorties'][0]
    sortie = {"id": sortie['_id']['$oid'],
                    "activation": sortie['Activation']['$date']['$numberLong'],
                    "expiry": sortie['Expiry']['$date']['$numberLong'],
                    "boss": sortieData['bosses'][sortie['Boss']]['name'],
                    "missions": [
                        {
                        "missionType": missionTypes[sortie['Variants'][0]['missionType']],
                        "modifierType": sortieData['modifierTypes'][sortie['Variants'][0]['modifierType']],
                        "modifierDescription": sortieData['modifierDescription'][sortie['Variants'][0]['modifierType']],
                        "node": solNodes[sortie['Variants'][0]['node']]
                        },
                        {
                        "missionType": missionTypes[sortie['Variants'][1]['missionType']],
                        "modifierType": sortieData['modifierTypes'][sortie['Variants'][1]['modifierType']],
                        "modifierDescription": sortieData['modifierDescription'][sortie['Variants'][1]['modifierType']],
                        "node": solNodes[sortie['Variants'][1]['node']]
                        },
                        {
                        "missionType": missionTypes[sortie['Variants'][2]['missionType']],
                        "modifierType": sortieData['modifierTypes'][sortie['Variants'][2]['modifierType']],
                        "modifierDescription": sortieData['modifierDescription'][sortie['Variants'][2]['modifierType']],
                        "node": solNodes[sortie['Variants'][2]['node']]
                        }
                    ]
                    }
    return sortie

def request_baro():
    baroapi = requests.get('http://content.warframe.com/dynamic/worldState.php').json()['VoidTraders'][0]
    x = False
    if datetime.datetime.now() > datetime.datetime.fromtimestamp(int(baroapi['Activation']['$date']['$numberLong'])/1000):
        x = True
    voidTrader = {'id': baroapi['_id']['$oid'],
                  'activation': int(baroapi['Activation']['$date']['$numberLong'])/1000,
                  'expiry': int(baroapi['Expiry']['$date']['$numberLong'])/1000,
                  'active': x,
                  'location': solNodes[baroapi['Node']]['node']+' ({})'.format(solNodes[baroapi['Node']]['planet']),
                  'inventory': []
                  }
    if voidTrader['active'] == True:
        for i in baroapi['Manifest']:
            i = {'item':lang[i['ItemType'].lower()],
                 'ducats':i['PrimePrice'],
                 'credits':i['RegularPrice']}
            voidTrader['inventory'].append(i)
    return voidTrader

async def baro_post_task():
    global OldBaro
    global CurrentBaro
    global voidTrader
    CurrentBaro = request_baro()
    if not CurrentBaro == OldBaro: ## prevents duplicate posting
        if CurrentBaro['active'] == True:
            for i in servers:
                x = prettytable.PrettyTable(["Item", "Ducats", "Credits"])
                x.sortby = "Ducats"
                x.reversesort=True
                for item in CurrentBaro['inventory']:
                    x.add_row((item["item"], item["ducats"], item["credits"]))
                try:
                    async with aiohttp.ClientSession() as session:
                        webhook = Webhook.from_url(i['barowebhook'], adapter=AsyncWebhookAdapter(session))
                        await webhook.send(content='```'+str(x)+'```', avatar_url='https://content.warframe.com/MobileExport/Lotus/Interface/Icons/Player/BaroKiteerAvatar.png')
                except:
                    pass
        OldBaro = CurrentBaro ### setting old baro to the one that was just posted, so it doesnt send duplicate

async def gftl():
    global gftla
    global gftlb
    gftlb = []
    alerts = requests.get('https://api.warframestat.us/pc/alerts').json()
    for alert in alerts:
        if alert['id'] not in gftla:
            if alert['mission']['description'] == 'Gift From The Lotus':
                timestamp = datetime.datetime.fromisoformat(alert['expiry'][:-1])
                embed = discord.Embed(title=alert['mission']['description'],
                                      colour=discord.Colour(0x9013fe),
                                      timestamp=timestamp)
                embed.add_field(name='Node', value=alert['mission']['node'], inline=True)
                embed.add_field(name='Mission Type', value=alert['mission']['type'], inline=True)
                embed.add_field(name='Faction', value=alert['mission']['faction'], inline=True)
                embed.add_field(name='Level', value=str(alert['mission']['minEnemyLevel'])+' - '+str(alert['mission']['maxEnemyLevel']), inline=True)
                embed.add_field(name='Reward', value=alert['mission']['reward']['asString'], inline=False)
                embed.set_footer(text=alert['id']+' / Ends')
                for i in servers:
                    try:
                        async with aiohttp.ClientSession() as session:
                            webhook = Webhook.from_url(i['giftinvasionswebhook'], adapter=AsyncWebhookAdapter(session))
                            await webhook.send(embed=embed)
                    except:
                        pass
            gftla.append(alert['id'])
        gftlb.append(alert['id'])
    for i in gftla:
        if i not in gftlb:
            gftla.remove(i)

async def rt():
    global redtext
    xd = requests.get('https://10o.io/EE.log').json()
    y = []
    for i in xd:
        if (i not in redtext) and ('IRC in: :[' in i['message']):
            haha = re.search("IRC in: :([^ ]+) WALLOPS \:(.*)", i['message'])
            for i in servers:
                try:
                    async with aiohttp.ClientSession() as session:
                        webhook = Webhook.from_url(i['redtextwebhook'], adapter=AsyncWebhookAdapter(session))
                        await webhook.send('```diff\n- '+haha[2]+'```')
                except:
                    pass
            redtext.append(i)
        y.append(i)
    for i in redtext:
        if i not in y:
            redtext.remove(i)

async def inv():
    global inva
    global invb
    invasions = requests.get('https://api.warframestat.us/pc/invasions').json()
    for invasion in invasions:
        if invasion['id'] not in inva:
            node = invasion['node']
            if invasion['vsInfestation'] == True:
                attackReward = 'None'
                defendReward = invasion['defenderReward']['countedItems'][0]
                for i in invasionitem:
                    if i in defendReward['type'] or i in defendReward['type']:
                        embed = discord.Embed(title=invasion['node'],
                                              colour=discord.Colour(invasion['attackerReward']['color']))
                        embed.add_field(name=invasion['attackingFaction'], value=attackReward, inline=False)
                        embed.add_field(name=invasion['defendingFaction'], value=defendReward['type'], inline=False)
                        embed.set_author(name=invasion['desc'])
                        embed.set_thumbnail(url=invasion['defenderReward']['thumbnail'])
                        embed.set_footer(text=invasion['id'])
                        for i in servers:
                            try:
                                async with aiohttp.ClientSession() as session:
                                    webhook = Webhook.from_url(i['giftinvasionswebhook'], adapter=AsyncWebhookAdapter(session))
                                    await webhook.send(embed=embed)
                            except:
                                pass
            else:
                defendReward = invasion['defenderReward']['countedItems'][0]
                attackReward = invasion['attackerReward']['countedItems'][0]
                for i in invasionitem:
                    if i in defendReward['type'] or i in defendReward['type']:
                        embed = discord.Embed(title=invasion['node'],
                                              colour=discord.Colour(1))
                        embed.add_field(name=invasion['attackingFaction'], value=attackReward['type'], inline=False)
                        embed.add_field(name=invasion['defendingFaction'], value=defendReward['type'], inline=False)
                        embed.set_author(name=invasion['desc'])
                        if i in defendReward['type']:
                            embed.set_thumbnail(url=invasion['defenderReward']['thumbnail'])
                        else:
                            embed.set_thumbnail(url=invasion['attackerReward']['thumbnail'])
                        embed.set_footer(text=invasion['id'])
                        for i in servers:
                            try:
                                async with aiohttp.ClientSession() as session:
                                    webhook = Webhook.from_url(i['giftinvasionswebhook'], adapter=AsyncWebhookAdapter(session))
                                    await webhook.send(embed=embed)
                            except:
                                pass
            inva.append(invasion['id'])
        invb.append(invasion['id'])
    for i in inva:
        if i not in invb:
            inva.remove(i)

def setup(bot):
    sched.add_job(baro_post_task, trigger='cron', minute='*', id='Baro', misfire_grace_time=60, replace_existing=True) # trigger every minute, works best cus cron
    sched.add_job(inv, trigger='cron', minute='*', id='Invasions', misfire_grace_time=60, replace_existing=True)
    sched.add_job(gftl, trigger='cron', minute='*', id='GFTL', misfire_grace_time=60, replace_existing=True)
    sched.add_job(rt, trigger='cron', minute='*', id='Redtext', misfire_grace_time=60, replace_existing=True)
    bot.add_cog(Warframe(bot))
