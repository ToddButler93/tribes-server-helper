import discord
from discord.ext import commands
from discord import app_commands
from typing import List
import json
import subprocess
import re
import aiohttp
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

role_error_string = "You do not have the required role to use this command."

mapchoice = 0

with open('server_data.json') as f:
    containers_data = json.load(f)
    containers = containers_data.get('containers', [])

    container_choices = []
    for container in containers:
        container_choices.append(app_commands.Choice(name=container["label"], value=container["name"]))

with open('config.json') as f:
    data = json.load(f)
    token = data["TOKEN"]
    watch_container = data["SERVER_TO_WATCH"]
    role_required = data["DISCORD_ROLE"]
    default_server = data["DEFAULT_SERVER"]
    num_player_text_server_down = data["NUM_PLAYERS_TEXT_SERVER_DOWN"]
    num_player_text_0 = data["NUM_PLAYERS_TEXT_0"]
    num_player_text_1 = data["NUM_PLAYERS_TEXT_1"]
    num_player_text_1_14 = data["NUM_PLAYERS_TEXT_1-14"]
    num_player_text_14 = data["NUM_PLAYERS_TEXT_14+"]

def has_role(member, role_name):
    """
    Check if a member has a specific role.
    """
    for role in member.roles:
        if role.name == role_name:  # You can also use role.id if you have the role's ID.
            return True
    return False

# Remove specified prefixes from map names
def remove_prefix(map_name):
    prefixes_to_remove = ["TrCTF-", "TrCTFBlitz-", "TrArena-"]
    for prefix in prefixes_to_remove:
        map_name = map_name.replace(prefix, "")
    # Add a space before capitalized letters and numbers
    map_name = re.sub(r"([a-zA-Z0-9])([A-Z0-9])", r"\1 \2", map_name)
    return map_name

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.tree.sync()
    bot.loop.create_task(update_activity())

@bot.tree.command(name="servers",description="Lists available game servers")
async def slash_list_servers(interaction:discord.Interaction):

    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    server_list = "\n".join([c["label"] for c in containers])
    
    embed = discord.Embed(title="Available Containers", description=server_list, color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status",description="Lists online game servers")
async def slash_status(interaction:discord.Interaction):

    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    try:
        # Use the subprocess module to run the "docker ps" command
        process = subprocess.Popen(["docker", "ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if stderr:
            raise Exception(stderr)
        
        # Use a regular expression to filter container names starting with 'taserver_' and remove the trailing "_[number]"
        container_names = [re.sub(r'_\d+$', '', line.strip()) for line in stdout.splitlines() if line.startswith("taserver_")]
        
        if not container_names:
            embed = discord.Embed(title="No Servers Online", description='No running servers found.', color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
        else:
            # Create a formatted message with the container names
            container_list = "\n".join(container_names)
            embed = discord.Embed(title="Running Servers", description=container_list, color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
    
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")

@bot.tree.command(name='restart', description='Restart a game server')
@app_commands.choices(server=container_choices)
async def slash_restart(interaction:discord.Interaction, server: app_commands.Choice[str] = default_server):
    if (server != default_server):
        server = server.value
    print (server)
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == server), None)
    
    if not container_info:
        embed = discord.Embed(title="Error", description=f"Server {server} not found.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    port = container_info['port']
    
    embed = discord.Embed(title="Restarting Server", description=f"Server {container_info['label']} will be restarted.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

    docker_restart_command = ['docker', 'restart', f"taserver_{server}_{port}"]
    subprocess.run(docker_restart_command)
    
    
    embed = discord.Embed(title=f"Server {container_info['label']} has been restarted.", color=discord.Color.green())
    await interaction.followup.send(embed=embed)


@bot.tree.command(name='stop', description='Stop a server')
@app_commands.choices(server=container_choices)
async def slash_stop(interaction:discord.Interaction, server: app_commands.Choice[str] = default_server):
    if (server != default_server):
        server = server.value
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == server), None)

    if not container_info:
        embed = discord.Embed(title="Error", description=f"Server {server} not found.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    port = container_info['port']

    embed = discord.Embed(title="Stopping Server", description=f"Server {container_info['label']} will be stopped.", color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)

    docker_stop_command = ['docker', 'stop', f"taserver_{server}_{port}"]
    subprocess.run(docker_stop_command)
    
    
    embed = discord.Embed(title="Server stopped", description=f"Server {container_info['label']} has been stopped.", color=discord.Color.green())
    await interaction.followup.send(embed=embed)


@bot.tree.command(name='listmaps', description='List maps for a game server')
@app_commands.choices(server=container_choices)
async def slash_listmaps(interaction:discord.Interaction, server: app_commands.Choice[str] = default_server):
    if (server != default_server):
        server = server.value
    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    # Check if the specified container name is valid
    container_info = next((c for c in containers if c["name"] == server), None)
    
    if not container_info:
        embed = discord.Embed(title="Error", description=f"Server {container_info['label']} not found.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    map_rotation_for_container = container_info.get("maps", [])
    
    if not map_rotation_for_container:
        embed = discord.Embed(title="Maps for Server", description=f"No maps found for {container_info['label']}.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return

    # Create a table-like structure for the list of maps
    map_table = "\n".join([f"{index + 1}. {remove_prefix(map_name)}" for index, map_name in enumerate(map_rotation_for_container)])
    
    embed = discord.Embed(title=f"Maps for {container_info['label']}", description=map_table, color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

def SelectMap(container_info):

    class Select(discord.ui.Select):
        def __init__(self): # the decorator that lets you specify the properties of the select menu
            options=[
                discord.SelectOption(label=str(map_rotation_for_container[index]), value=index) 
                for index in range(len(map_rotation_for_container))
            ]
            super().__init__(placeholder="Which map should the server be changed to?",options=options)
        
        async def callback(self, interaction: discord.Interaction): # the function called when the user is done selecting options
            mapchoice = self.values[0]
            
            map_index = mapchoice

            new_map_override = ""

            map_rotation_state = {
                "next_map_index": int(map_index),
                "next_map_override": new_map_override
            }

            file_path = f"/home/sandraker/{container_info['name']}_maprotationstate.json"
            with open(file_path, 'w') as f:
                json.dump(map_rotation_state, f)

            embed = discord.Embed(title=f"Map set to: {str(map_rotation_for_container[int(map_index)])}", description=f"{container_info['label']} will be restarted.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

            docker_cp_command = ['docker', 'cp', file_path, f"taserver_{container_info['name']}_{port}:/app/taserver/data/maprotationstate.json"]
            subprocess.run(docker_cp_command)

            docker_restart_command = ['docker', 'restart', f"taserver_{container_info['name']}_{port}"]
            subprocess.run(docker_restart_command)

            embed = discord.Embed(title="Server has restarted", description=f"{map_rotation_for_container[int(map_index)]} for {container_info['label']}.", color=discord.Color.green())
            await interaction.followup.send(embed=embed)

    class SelectMapView(discord.ui.View):
        def __init__(self, timeout = 25):
            super().__init__(timeout=timeout)
            self.add_item(Select())
    
    
    port = container_info['port']
    map_rotation_for_container = container_info.get("maps", [])
            
    selectView = SelectMapView()

    return selectView

@bot.tree.command(name='setmap', description='Set a map for a server')
@app_commands.choices(server=container_choices)
async def slash_setmap(interaction: discord.Interaction, server: app_commands.Choice[str] = default_server):
    if (server != default_server):
        server = server.value

    member = interaction.user
    if not any(role.name == role_required for role in member.roles):
        embed = discord.Embed(title="Error", description=role_error_string, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    container_info = next((c for c in containers if c["name"] == server), None)

    if not container_info:
        embed = discord.Embed(title="Error", description=f"Server {server} not found.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    map_view = SelectMap(container_info)

    embed = discord.Embed(
        title=f"Select a map for {container_info['label']}",
        description="Choose a map from the dropdown menu below.",
        color=discord.Color.blue(),
    )

    await interaction.response.send_message(embed=embed, view=map_view)
    
    # Wait for the user to make a selection
    try:
        interaction = await bot.wait_for("select_option", check=lambda i: i.component.custom_id == "map_index", timeout=60)
    except asyncio.TimeoutError:
        # Handle timeout if the user doesn't make a selection
        await interaction.followup.send("Map selection timed out.", ephemeral=True)
        return

@bot.event
async def on_slash_command_error(ctx, error):
    embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
    await ctx.send(embed=embed)



async def update_activity():
    while True:
        async with aiohttp.ClientSession() as session:
            
            async with session.get("http://ta.dodgesdomain.com:9080/detailed_status") as response:
                if response.status == 200:
                    html_content = await response.text()
                    num_players = -1
                    activity_type = discord.ActivityType.playing
                    activity_name = num_player_text_server_down
                    # Check if the watched server is present in the HTML
                    if f'"name": "{watch_container}"' in html_content:
                        # Extract the list of players within the "players" array
                        players_match = re.search(r'"players": \[([^]]+)\]', html_content)
                        if players_match:
                            players_list = players_match.group(1).split(',')
                            num_players = len(players_list)
                        else:
                            num_players = 0
                        

                    # TODO Allow a few configurable strings/activity types/cutoffs
                    if num_players == 0:
                        activity_type=discord.ActivityType.playing
                        activity_name = num_player_text_0
                    elif num_players == 1:
                        activity_name = f"{players_list[0]} {num_player_text_1}"
                    elif num_players < 1 & num_players > 14:
                        activity_name = f"{num_players} {num_player_text_1_14}"
                    elif num_players > 14:
                        activity_type=discord.ActivityType.playing
                        activity_name = f"{num_player_text_14}"

                    await bot.change_presence(activity=discord.Activity(type=activity_type, name=f"{activity_name}"))
        await asyncio.sleep(60)  # Wait for 1 minute

bot.run(token)
