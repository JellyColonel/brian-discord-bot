# brian-discord-bot/config.py

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
    raise ValueError(
        "No Discord token found. Please add DISCORD_TOKEN to your .env file.")
if SERVER_ID == 0:
    raise ValueError(
        "No Server ID found. Please add SERVER_ID to your .env file.")

# Appearance
EMBED_COLOR = disnake.Color.blurple()  # Default embed color
ERROR_COLOR = disnake.Color.red()
SUCCESS_COLOR = disnake.Color.green()
INFO_COLOR = disnake.Color.blue()

# Bot feature flags - enable/disable features easily
FEATURES = {
    'FUN': os.getenv('FEATURE_FUN', 'True').lower() == 'true',
    'LOGGING': os.getenv('FEATURE_LOGGING', 'True').lower() == 'true',
    'STAFF_LISTINGS': os.getenv('FEATURE_STAFF_LISTINGS', 'True').lower() == 'true',
    # Add more features as needed
}

# Configure specific features
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))

# Staff listings configuration
HIGH_STAFF_LISTING_CHANNEL_ID = int(
    os.getenv('HIGH_STAFF_LISTING_CHANNEL_ID', '0'))

# Role IDs for staff listings
ROLE_IDS = {
    'CHIEF_DOCTOR': int(os.getenv('ROLE_CHIEF_DOCTOR', '0')),
    'DEPUTY_CHIEF_DOCTOR': int(os.getenv('ROLE_DEPUTY_CHIEF_DOCTOR', '0')),
    'HOSPITAL_MANAGER': int(os.getenv('ROLE_HOSPITAL_MANAGER', '0')),
    'MANAGEMENT_STAFF': int(os.getenv('ROLE_MANAGEMENT_STAFF', '0')),
    'HIGH_STAFF': int(os.getenv('ROLE_HIGH_STAFF', '0')),  # Add this line
    'HAD_DEPARTMENT': int(os.getenv('ROLE_HAD_DEPARTMENT', '0')),
    'PM_DEPARTMENT': int(os.getenv('ROLE_PM_DEPARTMENT', '0')),
    'DI_DEPARTMENT': int(os.getenv('ROLE_DI_DEPARTMENT', '0')),
    'PSED_DEPARTMENT': int(os.getenv('ROLE_PSED_DEPARTMENT', '0')),
    'FD_DEPARTMENT': int(os.getenv('ROLE_FD_DEPARTMENT', '0')),
}

# Hospital managers' IDs (hardcoded)
HOSPITAL_MANAGERS = {
    'EAST_LOS_SANTOS': 741968124529606657,  # Anastasia Heavenly
    'SANDY_SHORES': 421692991493636096,     # Ben Cole
    'THE_BAY_CARE': 483906743567646722,     # Yaya Revo
}

# Department information - order matters for display
DEPARTMENTS = [
    {
        'short': 'HAD',
        'full': 'Hospital Administration Department',
        'channel_id': int(os.getenv('CHANNEL_HAD_DEPARTMENT', '0'))
    },
    {
        'short': 'PM',
        'full': 'Paramedic',
        'channel_id': int(os.getenv('CHANNEL_PM_DEPARTMENT', '0'))
    },
    {
        'short': 'DI',
        'full': 'Department of Internship',
        'channel_id': int(os.getenv('CHANNEL_DI_DEPARTMENT', '0'))
    },
    {
        'short': 'PSED',
        'full': 'Psychological And Sanitary Epidemiological Department',
        'channel_id': int(os.getenv('CHANNEL_PSED_DEPARTMENT', '0'))
    },
    {
        'short': 'FD',
        'full': 'Fire Department',
        'channel_id': int(os.getenv('CHANNEL_FD_DEPARTMENT', '0'))
    },
]
