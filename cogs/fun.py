# brian-discord-bot/cogs/fun.py

import disnake
from disnake.ext import commands

class Fun(commands.Cog):
    """Fun commands for your server"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Add fun commands here later
    
def setup(bot):
    bot.add_cog(Fun(bot))