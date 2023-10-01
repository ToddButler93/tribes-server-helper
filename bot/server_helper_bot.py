import discord
from discord.ext import commands, tasks
import re
import aiohttp
import asyncio
from cogs.server_commands import ServerCommandsCog
from cogs.map_commands import MapCommandsCog
from config import TOKEN, SERVER_TO_WATCH, DISCORD_ROLE

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Starting up..."))
    
    # Load Cogs (command modules)
    await bot.add_cog(ServerCommandsCog(bot))
    await bot.add_cog(MapCommandsCog(bot))
    
    await bot.tree.sync()
    # Start background tasks
    update_activity.start()

@tasks.loop(minutes=1)
async def update_activity():
    await bot.wait_until_ready()
    while True:
        async with aiohttp.ClientSession() as session:
            
            async with session.get("http://ta.dodgesdomain.com:9080/detailed_status") as response:
                if response.status == 200:
                    html_content = await response.text()
                    num_players = -1
                    activity_type = discord.ActivityType.playing
                    activity_name = 'Servers down/restarting'
                    # Check if the watched server is present in the HTML
                    if f'"name": "{SERVER_TO_WATCH}"' in html_content:
                        if players_match := re.search(
                            r'"players": \[([^]]+)\]', html_content
                        ):
                            players_list = players_match[1].split(',')
                            num_players = len(players_list)
                        else:
                            num_players = 0


                    # TODO Allow a few configurable strings/activity types/cutoffs
                    if num_players == 0:
                        activity_type=discord.ActivityType.playing
                        activity_name = 'UDK 2011'
                    elif num_players == 1:
                        activity_name = f"{players_list[0]} test maps."
                    elif num_players < 1 & num_players > 14:
                        activity_name = f"{num_players} players test maps"
                    elif num_players > 14:
                        activity_type=discord.ActivityType.playing
                        activity_name = " players playing pugs"

                    await bot.change_presence(activity=discord.Activity(type=activity_type, name=f"{activity_name}"))
        await asyncio.sleep(60)  # Wait for 1 minute

@bot.event
async def on_slash_command_error(ctx, error):
    embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
