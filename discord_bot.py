import discord
from discord.ext import commands
import json
import subprocess
import re
import aiohttp
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

map_rotation = [
    "TrCTF-TreacherousPass",
    "TrCTF-Eclipse",
    "TrCTF-Polaris",
    "TrCTF-Ascent",
    "TrCTF-Oceanus",
    "TrCTF-Meridian",
    "TrCTFBlitz-AirArena",
    "TrCTFBlitz-MazeRunner",
    "TrCTF-Andromeda",
    "TrCTF-DesertedValley2",
    "TrArena-Arenaxd",
    "TrArena-ElysianBattleground"
]

with open('config.json') as f:
    data = json.load(f)
    token = data["TOKEN"]
    channel_id = data["CHANNEL_ID"]
    pugbot_id = data["PUGBOT_ID"]
    server_id = data["SERVER_ID"]

container_name = "taserver_maptest_14"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    bot.loop.create_task(update_activity())

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots
    
    if message.channel.id == channel_id and message.content.startswith('!'):
        content = message.content[1:]  # Remove the '!' from the message
        await process_command(message, content)
    
    await bot.process_commands(message)  # Process other commands

async def process_command(message, content):
    commands_mapping = {
        'restart': restart_command,
        'help': help_command,
        'setmap': setmap_command,
        'listmaps': listmaps_command,  # Add the new command here
    }


    command_parts = content.split(' ')
    command_name = command_parts[0]
    
    if command_name in commands_mapping:
        command_function = commands_mapping[command_name]
        await command_function(message, command_parts[1:])
    else:
        await message.channel.send("Unknown command. Use `!help` for a list of commands.")

async def restart_command(message, args):
    docker_restart_command = ['docker', 'restart', container_name]
    subprocess.run(docker_restart_command)
    
    await message.channel.send(f"Container '{container_name}' has been restarted.")

async def help_command(message, args):
    help_text = (
        "Available commands:\n"
        "!restart: Restart server.\n"
        "!listmaps: Shows map rotation index.\n"
        "!setmap [index]: Set the map rotation based on index."
        )
    await message.channel.send(help_text)

async def listmaps_command(message, args):

    map_list = "\n".join([f"{index}: {map_name}" for index, map_name in enumerate(map_rotation)])
    await message.channel.send("Available maps:\n" + map_list)


async def setmap_command(message, args):

    if len(args) < 1 or len(args) > 1:
        await message.channel.send("Usage: `!setmap [map_index]`")
        return
    
    map_index = int(args[0])

    docker_ps_command = ['docker', 'ps', '--format', '{{.Names}}']
    running_containers = subprocess.run(docker_ps_command, capture_output=True, text=True).stdout.split('\n')
    running_containers = [name.strip() for name in running_containers if name.strip()]


    if container_name not in running_containers:
        await message.channel.send(f"Container '{container_name}' is not running.")
        return

    if map_index < 0 or map_index >= len(map_rotation):
        map_list = "\n".join([f"{index}: {map_name}" for index, map_name in enumerate(map_rotation)])
        await message.channel.send(f"Invalid map index. Choose a map from the following list:\n{map_list}")
        return

    # Modify the maprotationstate.json data
    new_map_index = map_index
    new_map_override = ""

    map_rotation_state = {
        "next_map_index": new_map_index,
        "next_map_override": new_map_override
    }

    # Write the map rotation state to a file on the host machine
    file_path = '/home/sandraker/maprotationstate.json'
    with open(file_path, 'w') as f:
        json.dump(map_rotation_state, f)

    # Copy the file into the Docker container
    docker_cp_command = ['docker', 'cp', file_path, f'{container_name}:/app/taserver/data/maprotationstate.json']
    subprocess.run(docker_cp_command)

    # Restart the selected Docker container
    docker_restart_command = ['docker', 'restart', container_name]
    subprocess.run(docker_restart_command)

    await message.channel.send(f"Map set to: {map_rotation[map_index]}. Container '{container_name}' will be restarted.")

async def update_activity():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://ta.dodgesdomain.com:9080/detailed_status") as response:
                if response.status == 200:
                    html_content = await response.text()
                    num_players = 0
                    # Check if the "Unreleased Map Testing" server is present in the HTML
                    if '"name": "Unreleased Map Testing"' in html_content:
                        # Extract the list of players within the "players" array
                        players_match = re.search(r'"players": \[([^]]+)\]', html_content)
                        if players_match:
                            players_list = players_match.group(1).split(',')
                            num_players = len(players_list)
                        else:
                            num_players = 0
                    else:
                        num_players = 0

                    activity_type=discord.ActivityType.watching

                    if num_players == 0:
                        activity_type=discord.ActivityType.playing
                        activity_name = "UDK 2011"
                    elif num_players == 1:
                        activity_name = f"{players_list[0]} test maps"
                    else:
                        activity_name = f"{num_players} players test maps"

                    await bot.change_presence(activity=discord.Activity(type=activity_type, name=f"{activity_name}"))
        await asyncio.sleep(60)  # Wait for 1 minute

bot.run(token)
