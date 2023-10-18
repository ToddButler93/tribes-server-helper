import discord
from discord.ext import commands
from discord import app_commands
from config import DISCORD_ROLE, DEFAULT_SERVER, container_choices, containers 
from utils import has_role
import subprocess
import re

class ServerCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="servers", description="Lists available game servers")
    async def slash_list_servers(self, interaction:discord.Interaction):
        member = interaction.user
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        server_list = "\n".join([c["label"] for c in containers])

        embed = discord.Embed(title="Available Containers", description=server_list, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Lists online game servers")
    async def slash_status(self, interaction:discord.Interaction):
        member = interaction.user
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        try:
            # Use the subprocess module to run the "docker ps" command
            process = subprocess.Popen(["docker", "ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if stderr:
                raise Exception(stderr)

            if container_names := [
                re.sub(r'_\d+$', '', line.strip())
                for line in stdout.splitlines()
                if line.startswith("taserver_")
            ]:
                # Create a formatted message with the container names
                container_list = "\n".join(container_names)
                embed = discord.Embed(title="Running Servers", description=container_list, color=discord.Color.green())
            else:
                embed = discord.Embed(title="No Servers Online", description='No running servers found.', color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}")

    # Add more server-related commands as needed
    @app_commands.command(name='restart', description='Restart a game server')
    @app_commands.choices(server=container_choices)
    async def slash_restart(self, interaction:discord.Interaction, server: app_commands.Choice[str] = DEFAULT_SERVER):
        if (server != DEFAULT_SERVER):
            server = server.value
        print (server)
        member = interaction.user
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
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


    @app_commands.command(name='stop', description='Stop a server')
    @app_commands.choices(server=container_choices)
    async def slash_stop(self, interaction:discord.Interaction, server: app_commands.Choice[str] = DEFAULT_SERVER):
        if (server != DEFAULT_SERVER):
            server = server.value
        member = interaction.user
        if all(role.name != DISCORD_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
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