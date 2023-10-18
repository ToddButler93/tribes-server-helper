import discord
from discord.ext import commands
from discord import app_commands

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient

from config import VM_MANAGEMENT_ROLE, AZ_TENANT_ID, AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_SUBSCRIPTION_ID, AZ_RESOURCE_GROUP_NAME, AZ_VM_NAME

az_credential = ClientSecretCredential(AZ_TENANT_ID, AZ_CLIENT_ID, AZ_CLIENT_SECRET)
az_compute_client = ComputeManagementClient(az_credential, AZ_SUBSCRIPTION_ID)

class VMCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="launchmixer", description="Starts the Mixer VM")
    async def slash_start_mixer_vm(self, interaction:discord.Interaction):

        member = interaction.user
        if all(role.name != VM_MANAGEMENT_ROLE for role in member.roles):
            embed = discord.Embed(title="Error", description='You do not have permission to use this command', color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="Mixer VM Booting Up", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
        
        async_vm_start = az_compute_client.virtual_machines.begin_start(
            AZ_RESOURCE_GROUP_NAME, AZ_VM_NAME)
        async_vm_start.wait()