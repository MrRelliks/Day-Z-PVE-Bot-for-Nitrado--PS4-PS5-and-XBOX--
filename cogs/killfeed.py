"""
MIT License

Copyright (c) 2020 Victor Cortez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from discord.ext import commands, tasks
from config import Config
from os import path

import aiohttp
import aiofiles
import asyncio
import logging
import random
import discord
import re
import requests
from requests.structures import CaseInsensitiveDict
import json
import math







class Killfeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reported = {}
        self.last_log = {}
        self.headers = {'Authorization': f'Bearer {Config.NITRADO_TOKEN}'}
        logging.basicConfig(level=logging.INFO)
    
    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("Started bot DayZ PVE Bot | Based on KilLFeef Bot Made by vic#1337")
        self.fetch_logs.start()
        self.OnlinePlayers.start()
        self.RestartServer.start()
        

    async def run_loop(self):
        coros = []
        #servers = list(Config.SERVERS.keys())

        nitrado_id = 12520701
        log = await self.download_logfile(Config.nitrado_id)

        if log:
            coros.append(self.check_log(Config.nitrado_id))
        
        await asyncio.gather(*coros)

    #This is a task to automate server restarts and send pings to Discord
    @tasks.loop(hours=12)
    async def RestartServer(self):
        restartchannel = self.bot.get_channel(Config.restartchannel)
        pingrole = 1088546845023797278
        amount = 50 #Increase this if you get more than 50 at a time
        await restartchannel.purge(limit=amount)
        await restartchannel.send(f"<@&{pingrole}> Restarting the server in 5 minutes.")
        await asyncio.sleep(300)
        url = "https://api.nitrado.net/services/12520701/gameservers/restart"
        headers = {'Authorization': f'Bearer {Config.NITRADO_TOKEN}'}
        request = requests.post(url,headers=headers)
        await asyncio.sleep(120)
        await restartchannel.send(f"<@&{pingrole}> Server is back up. Next restart in 12 hours.") # Change this if you change the hours
        


    @tasks.loop(seconds=120)
    async def OnlinePlayers(self):

        url = f"https://api.nitrado.net/services/{Config.nitrado_id}/gameservers/stats"
        headers = {'Authorization': f'Bearer {Config.NITRADO_TOKEN}'}

        request = requests.get(url,headers=headers)
        response = request.text
        output = json.loads(response)
        OnlineCHan = self.bot.get_channel(Config.PlayersOnlineChannel)
        

        players = math.floor(output['data']['stats']['currentPlayers'][-1][0])
        maxplayers = math.floor(output['data']['stats']['maxPlayers'][-1][0])
        await discord.CategoryChannel.edit(OnlineCHan, name = f" 🟢 {players} / {maxplayers} Players online")
        print(f"There are {players} / {maxplayers} Players online.")

    @tasks.loop(minutes=5)
    async def fetch_logs(self):
        await self.run_loop()
    
    async def check_log(self, nitrado_id: int):
        logging.info(f"Checking logfile for {Config.nitrado_id}")
        fp = path.abspath(path.join(path.dirname(__file__), "..", "files", f'{Config.nitrado_id}.ADM'))
        #channel = self.bot.get_channel(Config.SERVERS[nitrado_id])
        deaths = self.bot.get_channel(Config.Deaths)
        playerkillers = self.bot.get_channel(Config.PVP)
        other = self.bot.get_channel(Config.Other)
        locationschannel = self.bot.get_channel(Config.Locations)
        
        await locationschannel.purge(limit=200)
        
        if nitrado_id not in self.reported:
            self.reported[nitrado_id] = []
            
        if nitrado_id not in self.last_log:
            self.last_log[nitrado_id] = ""

        async with aiofiles.open(fp, mode="r") as f:
            async for line in f:
                if str(line) in self.reported[nitrado_id]:
                    continue
                
                if "AdminLog" in line:
                    if self.last_log[nitrado_id] != str(line):
                        self.last_log[nitrado_id] = str(line)
                        self.reported[nitrado_id] = []

                self.reported[nitrado_id].append(str(line))
               # Log any damage done by a player and alert us on Discord. 
               # if "hit by" in line:
                    #player = str(re.search(r'[\'"](.*?)[\'"]', line).group(1))

                if "pos" in line and "is unconscious" not in line and "hit by" not in line:
                    izurviveURL = "https://www.izurvive.com/#location="
                    
                    timestamp = str(re.search('(\\d+:\\d+:\\d+)', line).group(1))
                    player = str(re.search(r'[\'"](.*?)[\'"]', line).group(1))
                    coordinates1 = str(re.search(r'[\'<](.*?)[\',]', line).group(1))
                    coordinates2 = str(re.search(r'[\',](.*?)[\',]', line).group(1))
                    number = str(re.findall("\d+\.\d+", coordinates2))
                    
                    try:
                        coordinates3 = str(re.search(r"[\''](.*?)[\'']", number).group(1))
                        print(f"CURRENT POSITION({player}) - {izurviveURL}{coordinates1}%{coordinates3}")
                    except:
                        print("No position found")
                    
                    
                    message = f"{player}\n - <{izurviveURL}{coordinates1};{coordinates3}>"
                    embed = discord.Embed(
                            title=f"📌 {player} | {timestamp}",
                            description=f"<{izurviveURL}{coordinates1};{coordinates3}>",
                            color=0x7a00ff
                        )
                    
                    await locationschannel.send(embed=embed)
                
                    


                if "(DEAD)" in line or "committed suicide" in line:
                    timestamp = str(re.search('(\\d+:\\d+:\\d+)', line).group(1))
                    player_killed = str(re.search(r'[\'"](.*?)[\'"]', line).group(1))

                    if "committed suicide" in line:
                        embed = discord.Embed(
                            title=f"💀 Suicide | {timestamp}",
                            description=f"**{player_killed}** commited suicide",
                            color=0x7a00ff
                        )
                        await deaths.send(embed=embed)
                        await asyncio.sleep(2) # Avoid rate limits
                    elif "hit by explosion" in line:
                        explosion = str(re.search(r'\[HP: 0\] hit by explosion \((.*)\)', line).group(1))
                        embed = discord.Embed(
                            title=f"💀 Exploded | {timestamp}",
                            description=f"**{player_killed}** died from explosion ({explosion})",
                            color=0x7a00ff
                        )
                        await other.send(embed=embed)
                        await asyncio.sleep(2) # Avoid rate limits
                    elif "killed by Player" in line:
                        player_killer = str(re.search(r'killed by Player "(.*?)"', line).group(1))
                        coords = str(re.search(r'pos=<(.*?)>', line).group(1))
                        weapon = re.search(r' with (.*) from', line) or re.search(r'with (.*)', line)
                        weapon = str(weapon.group(1))
                        
                        try:
                            distance = round(float(re.search(r'from ([0-9.]+) meters', line).group(1)), 2)
                        except AttributeError:
                            distance = 0.0

                        embed = discord.Embed(
                            title=f"💀 PvP Kill | {timestamp}",
                            description=f"**{player_killer}** killed **{player_killed}**\n**Weapon**: `{weapon}` ({distance}m)\n**Location**: {coords}",
                            color=0x7a00ff
                        ).set_thumbnail(url=Config.EMBED_IMAGE)
                        rand_num = random.randint(1, 70)
                        if rand_num <= 2:
                            embed.description += "\n\nMade with :heart: by [Killfeed.me](https://killfeed.me)"
                        await playerkillers.send(embed=embed)
                        await asyncio.sleep(2) # Avoid rate limits
                    elif "bled out" in line:
                        embed = discord.Embed(
                            title=f"🩸 Bled Out | {timestamp}",
                            description=f"**{player_killed}** bled out",
                            color=0x7a00ff
                        )
                        await deaths.send(embed=embed)
                        await asyncio.sleep(2) # Avoid rate limits
                    
                    elif "hit by FallDamage" in line:
                        embed = discord.Embed(
                            title=f"💀 Fall Death | {timestamp}",
                            description=f"**{player_killed}** fell to their death!",
                            color=0x7a00ff
                        )
                        await other.send(embed=embed)
                        await asyncio.sleep(2) # Avoid rate limits
                
                    
                    
            logging.info(f"Finished checking logfile for {nitrado_id}")
    
    async def download_logfile(self, nitrado_id):
        logging.info(f"Downloading logfile for {nitrado_id}")

        async with aiohttp.ClientSession() as ses:
            async with ses.get(f'https://api.nitrado.net/services/{Config.nitrado_id}/gameservers', headers=self.headers) as r:
                if r.status != 200:
                    logging.error(f"Failed to get gameserver information ({Config.nitrado_id}) ({r.status})")
                    return False
                else:
                    json = await r.json()
                    
                    username = json['data']['gameserver']['username']
                    game = json["data"]["gameserver"]["game"].lower()

                    if game == "dayzps":
                        logpath = "dayzps/config/DayZServer_PS4_x64.ADM"
                    elif game == "dayzxb":
                        logpath = "dayzxb/config/DayZServer_X1_x64.ADM"
                    else:
                        log_path = ""
                        logging.error("This bot only supports: DayZ PS4 and DayZ Xbox")
                        return False
                    
                    async with ses.get(f'https://api.nitrado.net/services/{Config.nitrado_id}/gameservers/file_server/download?file=/games/{username}/noftp/{logpath}', headers=self.headers) as resp:
                        if resp.status != 200:
                            logging.error(f"Failed to get nitrado download URL! ({nitrado_id}) ({resp.status})")
                            return False
                        else:
                            json = await resp.json()
                            url = json["data"]["token"]["url"]

                            async with ses.get(url, headers=self.headers) as res:
                                if res.status != 200:
                                    logging.error(f'Failed to download nitrado log file! ({Config.nitrado_id}) ({res.status})')
                                    return False
                                else:
                                    fp = path.abspath(path.join(path.dirname(__file__), "..", "files", f'{Config.nitrado_id}.ADM'))
                                    async with aiofiles.open(fp, mode="wb+") as f:
                                        await f.write(await res.read())
                                        await f.close()
                                    logging.info(f"Successfully downloaded logfile for ({Config.nitrado_id})")
                                    return True

def setup(bot):
    bot.add_cog(Killfeed(bot))
