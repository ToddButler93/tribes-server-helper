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