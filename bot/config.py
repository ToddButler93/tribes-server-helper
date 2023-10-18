# config.py

import json
import os
from discord import app_commands

# Determine the absolute path to the data directory
data_dir = os.path.join(os.path.dirname(__file__), '../data')

# Specify the path to config.json
config_file_path = os.path.join(data_dir, 'config.json')

# Specify the path to config.json
server_config_file_path = os.path.join(data_dir, 'server_data.json')

# Specify the path to config.json
vm_config_file_path = os.path.join(data_dir, 'vm_data.json')

# Load the configuration data from config.json
with open(config_file_path) as f:
    config_data = json.load(f)

# Discord Bot Token
TOKEN = config_data.get('TOKEN', 'YOUR_DEFAULT_BOT_TOKEN')

# Discord Role Required to Use Bot Commands
DISCORD_ROLE = config_data.get('DISCORD_ROLE', 'YourDefaultRoleName')

# Server to Watch
SERVER_TO_WATCH = config_data.get('SERVER_TO_WATCH', 'YourDefaultServerName')

# Default Server
DEFAULT_SERVER = config_data.get('DEFAULT_SERVER', 'DefaultServerName')


with open(server_config_file_path) as f:
    containers_data = json.load(f)
    containers = containers_data.get('containers', [])

    container_choices = [
        app_commands.Choice(name=container["label"], value=container["name"])
        for container in containers
    ]


with open(vm_config_file_path) as f:
    vm_data = json.load(f)

    VM_MANAGEMENT_ROLE = vm_data.get('VM_MANAGEMENT_ROLE', 'YOUR_DEFAULT_VM_MANAGEMENT_ROLE')
    AZ_TENANT_ID = vm_data.get('AZ_TENANT_ID', 'YOUR_DEFAULT_AZ_TENANT_ID')
    AZ_CLIENT_ID = vm_data.get('AZ_CLIENT_ID', 'YOUR_DEFAULT_AZ_CLIENT_ID')
    AZ_CLIENT_SECRET = vm_data.get('AZ_CLIENT_SECRET', 'YOUR_DEFAULT_AZ_CLIENT_SECRET')
    AZ_SUBSCRIPTION_ID = vm_data.get('AZ_SUBSCRIPTION_ID', 'YOUR_DEFAULT_AZ_SUBSCRIPTION_ID')
    AZ_RESOURCE_GROUP_NAME = vm_data.get('AZ_RESOURCE_GROUP_NAME', 'YOUR_DEFAULT_AZ_RESOURCE_GROUP_NAME')
    AZ_VM_NAME = vm_data.get('AZ_VM_NAME', 'YOUR_DEFAULT_AZ_VM_NAME')