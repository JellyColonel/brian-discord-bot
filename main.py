# majestic-bot/main.py

import os
import disnake
from disnake.ext import commands
import config
import logging
from utils.logger import setup_logger

# Set up logging
logger = setup_logger()

def load_extensions(bot):
    """Load all extension cogs from the cogs directory"""
    count = 0
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f"Loaded extension: {filename[:-3]}")
                count += 1
            except Exception as e:
                logger.error(f"Failed to load extension {filename}: {e}")
    logger.info(f"Loaded {count} extensions")

def main():
    """Initialize and run the Discord bot"""
    # Set up intents (permissions for your bot)
    intents = disnake.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.messages = True
    
    # Create a bot instance with command prefix and intents
    bot = commands.Bot(
        command_prefix=config.COMMAND_PREFIX,
        intents=intents,
        test_guilds=[config.SERVER_ID],  # Single server for faster slash command registration
        help_command=None,  # We'll implement a custom help command
    )
    
    # Event: Bot is ready
    @bot.event
    async def on_ready():
        logger.info(f"{bot.user.name} has connected to Discord!")
        logger.info(f"Connected to {len(bot.guilds)} guild(s)")
        logger.info(f"Bot is serving {len(bot.users)} user(s)")
        
        # Set bot activity status
        await bot.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.listening, 
                name=f"{config.COMMAND_PREFIX}help"
            )
        )
    
    # Load extensions (cogs)
    load_extensions(bot)
    
    # Custom help command
    @bot.slash_command(name="help", description="Show help information for commands")
    async def help_command(
        inter, 
        module: str = commands.Param(default=None, description="Specific module to get help for")
    ):
        if module:
            # Show help for specific module
            for cog_name, cog in bot.cogs.items():
                if cog_name.lower() == module.lower():
                    embed = disnake.Embed(
                        title=f"{cog_name} Commands",
                        description=cog.__doc__ or "No description available",
                        color=config.EMBED_COLOR
                    )
                    
                    # Get commands from this cog
                    commands_list = cog.get_slash_commands()
                    if commands_list:
                        for cmd in commands_list:
                            embed.add_field(
                                name=f"/{cmd.name}",
                                value=cmd.description or "No description",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name="No commands",
                            value="This module has no slash commands",
                            inline=False
                        )
                    
                    return await inter.response.send_message(embed=embed)
            
            # If we get here, module wasn't found
            return await inter.response.send_message(
                f"Module '{module}' not found. Use `/help` to see all modules.",
                ephemeral=True
            )
        
        # Show general help with all modules
        embed = disnake.Embed(
            title=f"{bot.user.name} Help",
            description="Here are all the available command modules:",
            color=config.EMBED_COLOR
        )
        
        for cog_name, cog in bot.cogs.items():
            # Count commands in this cog
            cmd_count = len(cog.get_slash_commands())
            # Skip empty cogs or internal ones
            if cmd_count == 0 or cog_name.startswith("_"):
                continue
                
            embed.add_field(
                name=cog_name,
                value=f"{cog.__doc__ or 'No description'}\n*{cmd_count} command(s)*\nUse `/help {cog_name.lower()}` for details",
                inline=False
            )
        
        embed.set_footer(text=f"Type {config.COMMAND_PREFIX}help <command> for more info on a command")
        await inter.response.send_message(embed=embed)
    
    # Connection error handling
    @bot.event
    async def on_connect():
        logger.info("Bot connected to Discord")
    
    @bot.event
    async def on_disconnect():
        logger.warning("Bot disconnected from Discord")
    
    @bot.event
    async def on_resumed():
        logger.info("Bot connection resumed")
    
    # Run the bot
    bot.run(config.BOT_TOKEN)

if __name__ == "__main__":
    main()