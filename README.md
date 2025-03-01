# Modular Discord Bot

A highly modular Discord bot designed for single-server use with easy extensibility.

## Features

- **Modular Structure**: Easily add new commands and features
- **Feature Flags**: Enable/disable features without code changes
- **Slash Commands**: Modern Discord interaction support
- **Comprehensive Logging**: Both to console and file
- **Admin Commands**: Moderation tools included out of the box

## Required Bot Permissions

For full functionality, the bot requires these permissions:

- **Manage Messages** - For the `/purge` command to delete messages
- **Kick Members** - For the `/kick` command
- **Ban Members** - For the `/ban` command
- **Moderate Members** - For the `/timeout` command
- **Send Messages & Embed Links** - For basic functionality
- **Read Message History** - For various commands
- **Add Reactions** - For potential reaction features

## Setup

1. **Clone this repository**:

   ```bash
   git clone https://github.com/yourusername/your-bot-repo.git
   cd your-bot-repo
   ```

2. **Set up a virtual environment**:

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your bot**:

   - Copy `.env.template` to `.env`
   - Fill in your Discord bot token and server ID
   - Customize other settings as needed

5. **Add the bot to your server**:

   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Select your application/bot
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot` and `applications.commands`
   - Select the permissions listed in the "Required Bot Permissions" section above
   - Use the generated URL to add the bot to your server

6. **Run the bot**:

   ```bash
   python main.py
   ```

7. **Verify permissions**:
   - After adding the bot, check that it has all required permissions
   - If using commands like `/purge` in specific channels, ensure the bot has "Manage Messages" permission in those channels

## Creating New Extensions

To add new functionality to your bot, create a new Python file in the `cogs` directory:

1. Create a file like `cogs/my_feature.py`
2. Use this template for your cog:

```python
import disnake
from disnake.ext import commands

class MyFeature(commands.Cog):
    """Description of your feature"""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def my_command(self, inter):
        """Description of what this command does"""
        await inter.response.send_message("Hello from my custom command!")

def setup(bot):
    bot.add_cog(MyFeature(bot))
```

3. The bot will automatically load your new feature on startup
4. To reload while the bot is running, use the `/reload my_feature` command (owner only)

## Extension Ideas

Here are some ideas for extensions you might want to create:

- **Reaction Roles**: Let users self-assign roles by reacting to messages
- **Music Player**: Play music in voice channels
- **Server Stats**: Track and display server statistics
- **Custom Welcome**: Customize welcome messages with images
- **Giveaways**: Run and manage giveaways
- **Polls**: Create and manage polls with reactions
- **Reminders**: Let users set reminders
- **Auto-moderation**: Filter messages for specific content

## Folder Structure

```
my_discord_bot/
├── .env                    # Environment variables (token, etc.)
├── config.py               # Bot configuration
├── main.py                 # Entry point for the bot
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── logger.py           # Custom logging
│   └── helpers.py          # Helper functions
├── cogs/                   # Command modules
│   ├── __init__.py
│   ├── admin.py            # Admin commands
│   ├── fun.py              # Fun commands
│   └── custom_features.py  # Your special features
└── data/                   # Data storage (if needed)
    └── database.py         # Database interaction
```

## Troubleshooting

- **Bot doesn't start**: Check your `.env` file and ensure your token is correct
- **Slash commands not showing up**: Make sure your SERVER_ID is correct
- **Permission errors**: Check that the bot has the necessary permissions for each command
  - For `/purge` errors, ensure the bot has "Manage Messages" permission
  - For `/kick` or `/ban` errors, check role hierarchy (bot's role must be higher than target user's)
- **Command errors**: Check the logs folder for detailed error messages
