import discord
from discord.ext import commands
import json
import subprocess
import re
import aiohttp
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

with open('server_data.json') as f:
    containers_data = json.load(f)
    containers = containers_data.get('containers', [])

with open('config.json') as f:
    data = json.load(f)
    token = data["TOKEN"]
    watch_container = data["SERVER_TO_WATCH"]
    role_required = data["DISCORD_ROLE"]
    default_server = data["DEFAULT_SERVER"]

def has_role(member, role_name):
    """
    Check if a member has a specific role.
    """
    for role in member.roles:
        if role.name == role_name:  # You can also use role.id if you have the role's ID.
            return True
    return False

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.tree.sync()
    bot.loop.create_task(update_activity())

@bot.tree.command(name="servers",description="Lists available containers")
async def slash_list_servers(interaction:discord.Interaction):

    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        await interaction.response.send_message("You do not have the required role to use this command.")
        return
    
    server_list = "\n".join([c["name"] for c in containers])
    await interaction.response.send_message(f"Available containers:\n{server_list}")


@bot.tree.command(name='restart', description='Restart a server container')
async def slash_restart(interaction:discord.Interaction, container_name: str = default_server):

    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        await interaction.response.send_message("You do not have the required role to use this command.")
        return

    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == container_name), None)
    
    if not container_info:
        await interaction.response.send_message(f"Container '{container_name}' not found.")
        return
    
    port = container_info['port']
    
    await interaction.response.send_message(f"Container 'taserver_{container_name}_{port}' will be restarted.")

    docker_restart_command = ['docker', 'restart', f"taserver_{container_name}_{port}"]
    subprocess.run(docker_restart_command)
    
    await interaction.followup.send("Container has been restarted.")


@bot.tree.command(name='stop', description='Stop a server container')
async def slash_stop(interaction:discord.Interaction, container_name: str = default_server):
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        await interaction.response.send_message("You do not have the required role to use this command.")
        return
    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == container_name), None)

    if not container_info:
        await interaction.response.send_message(f"Container '{container_name}' not found.")
        return
    
    port = container_info['port']

    await interaction.response.send_message(f"Container '{container_name}' will be stopped.")

    docker_stop_command = ['docker', 'stop', f"taserver_{container_name}_{port}"]
    subprocess.run(docker_stop_command)
    
    await interaction.followup.send(f"Container '{container_name}' has been stopped.")

@bot.tree.command(name='listmaps', description='List maps for a server container')
async def slash_listmaps(interaction:discord.Interaction, container_name: str = default_server):
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        await interaction.response.send_message("You do not have the required role to use this command.")
        return
    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == container_name), None)
    
    if not container_info:
        await interaction.response.send_message(f"Container '{container_name}' not found.")
        return

    map_rotation_for_container = container_info.get("maps", [])
    
    map_list = "\n".join([f"{index}: {map_name}" for index, map_name in enumerate(map_rotation_for_container)])
    await interaction.response.send_message(f"Available maps for '{container_name}':\n{map_list}")

@bot.tree.command(name='setmap', description='Set a map for a server container')
async def slash_setmap(interaction:discord.Interaction, map_index: int, container_name: str = default_server):
    
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        await interaction.response.send_message("You do not have the required role to use this command.")
        return
    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == container_name), None)

    if not container_info:
        await interaction.response.send_message(f"Container '{container_name}' not found.")
        return
    
    port = container_info['port']
    map_rotation_for_container = container_info.get("maps", [])

    if map_index < 0 or map_index >= len(map_rotation_for_container):
        map_list = "\n".join([f"{index}: {map_name}" for index, map_name in enumerate(map_rotation_for_container)])
        await interaction.response.send_message(f"Invalid map index. Choose a map from the following list for '{container_name}':\n{map_list}")
        return

    # Modify the maprotationstate.json data for the specified container
    new_map_index = map_index
    new_map_override = ""

    map_rotation_state = {
        "next_map_index": new_map_index,
        "next_map_override": new_map_override
    }

    # Write the map rotation state to a file on the host machine
    file_path = f'/home/sandraker/{container_name}_maprotationstate.json'
    with open(file_path, 'w') as f:
        json.dump(map_rotation_state, f)

    await interaction.response.send_message(f"Map set to: {map_rotation_for_container[map_index]}. Container '{container_name}' will be restarted.")

    # Copy the file into the Docker container
    docker_cp_command = ['docker', 'cp', file_path, f'taserver_{container_name}_{port}:/app/taserver/data/maprotationstate.json']
    subprocess.run(docker_cp_command)

    # Restart the specified Docker container
    docker_restart_command = ['docker', 'restart', f"taserver_{container_name}_{port}"]
    subprocess.run(docker_restart_command)

    await interaction.followup.send(f"{container_name} has been restarted on {map_rotation_for_container[map_index]}.")

@bot.event
async def on_slash_command_error(ctx, error):
    await ctx.send(f"An error occurred: {str(error)}")

async def update_activity():
    while True:
        async with aiohttp.ClientSession() as session:
            
            async with session.get("http://ta.dodgesdomain.com:9080/detailed_status") as response:
                if response.status == 200:
                    html_content = await response.text()
                    num_players = 0
                    # Check if the watched server is present in the HTML
                    if f'"name": "{watch_container}"' in html_content:
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

                    # TODO Allow a few configurable strings/activity types/cutoffs
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
