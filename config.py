# majestic-bot/config.py

import os
from dotenv import load_dotenv
import disnake

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = int(os.getenv('SERVER_ID', '0'))  # Your server ID
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
OWNER_IDS = [int(id.strip()) for id in os.getenv('OWNER_IDS', '0').split(',')]

# Make sure critical values are set
if not BOT_TOKEN:
    raise ValueError("No Discord token found. Please add DISCORD_TOKEN to your .env file.")
if SERVER_ID == 0:
    raise ValueError("No Server ID found. Please add SERVER_ID to your .env file.")

# Appearance
EMBED_COLOR = disnake.Color.blurple()  # Default embed color
ERROR_COLOR = disnake.Color.red()
SUCCESS_COLOR = disnake.Color.green()
INFO_COLOR = disnake.Color.blue()

# Bot feature flags - enable/disable features easily
FEATURES = {
    'WELCOME_MESSAGES': os.getenv('FEATURE_WELCOME_MESSAGES', 'True').lower() == 'true',
    'LOGGING': os.getenv('FEATURE_LOGGING', 'True').lower() == 'true',
    'AUTO_ROLES': os.getenv('FEATURE_AUTO_ROLES', 'False').lower() == 'true',
    # Add more features as needed
}

# Configure specific features
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
DEFAULT_ROLE_ID = int(os.getenv('DEFAULT_ROLE_ID', '0'))