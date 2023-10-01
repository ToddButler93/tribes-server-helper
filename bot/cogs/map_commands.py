import discord
from discord.ext import commands
from discord import app_commands
import json
import subprocess
from config import DISCORD_ROLE, DEFAULT_SERVER, data_dir, container_choices, containers 
from utils import has_role
from utils import remove_prefix
#from server_commands import ServerCommandsCog  # Import ServerCommandsCog for server data

class MapCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='listmaps', description='List maps for a game server')
    @app_commands.choices(server=container_choices)
    async def slash_listmaps(self, interaction:discord.Interaction, server: app_commands.Choice[str] = DEFAULT_SERVER):
        if (server != DEFAULT_SERVER):
            server = server.value
        member = interaction.user

        #TODO Seperate into it's own function
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
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

    

    @app_commands.command(name='setmap', description='Set a map for a server')
    @app_commands.choices(server=container_choices)
    async def slash_setmap(self, interaction: discord.Interaction, server: app_commands.Choice[str] = DEFAULT_SERVER):
        if (server != DEFAULT_SERVER):
            server = server.value

        member = interaction.user
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
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


#TODO Seperate into it's own file (views.py)
# Add more map-related commands as needed
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

            file_path = f"{data_dir}/temp/{container_info['name']}_maprotationstate.json"
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
        def __init__(self, timeout = 15):
            super().__init__(timeout=timeout)
            self.add_item(Select())


    port = container_info['port']
    map_rotation_for_container = container_info.get("maps", [])

    return SelectMapView()