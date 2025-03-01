# brian-discord-bot/cogs/fun.py

import disnake
from disnake.ext import commands
import random
import asyncio
import math

class Fun(commands.Cog):
    """Fun and entertaining commands to spice up your server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ongoing_games = {}
    
    @commands.slash_command()
    async def coinflip(self, inter):
        """Flip a coin and see heads or tails!"""
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        await inter.response.send_message(f"🎲 The coin landed on: **{result}**!")
    
    @commands.slash_command()
    async def roll(
        self, 
        inter, 
        sides: int = commands.Param(description="Number of sides on the die", default=6, ge=2, le=100)
    ):
        """Roll a die with a specified number of sides"""
        roll_result = random.randint(1, sides)
        await inter.response.send_message(f"🎲 You rolled a {sides}-sided die and got: **{roll_result}**!")
    
    @commands.slash_command()
    async def rps(self, inter):
        """Play Rock, Paper, Scissors against the bot"""
        # Create buttons for Rock, Paper, Scissors
        view = disnake.ui.View()
        
        async def rps_callback(button_inter, choice):
            # Bot's choice
            bot_choices = ["🪨 Rock", "📄 Paper", "✂️ Scissors"]
            bot_choice = random.choice(bot_choices)
            
            # Determine winner
            user_choice = choice
            result_map = {
                "🪨 Rock": {
                    "🪨 Rock": "It's a tie!",
                    "📄 Paper": "You lose! Paper covers Rock.",
                    "✂️ Scissors": "You win! Rock breaks Scissors."
                },
                "📄 Paper": {
                    "🪨 Rock": "You win! Paper covers Rock.",
                    "📄 Paper": "It's a tie!",
                    "✂️ Scissors": "You lose! Scissors cut Paper."
                },
                "✂️ Scissors": {
                    "🪨 Rock": "You lose! Rock breaks Scissors.",
                    "📄 Paper": "You win! Scissors cut Paper.",
                    "✂️ Scissors": "It's a tie!"
                }
            }
            
            result = result_map[user_choice][bot_choice]
            
            await button_inter.response.edit_message(
                content=f"**You chose {user_choice}**\n**I chose {bot_choice}**\n\n{result}",
                view=None
            )
        
        # Create buttons for each choice
        for choice in ["🪨 Rock", "📄 Paper", "✂️ Scissors"]:
            button = disnake.ui.Button(
                label=choice.split()[1], 
                custom_id=f"rps_{choice}", 
                style=disnake.ButtonStyle.primary
            )
            
            async def create_callback(choice):
                async def callback(inter):
                    await rps_callback(inter, choice)
                return callback
            
            button.callback = create_callback(choice)
            view.add_item(button)
        
        await inter.response.send_message(
            "Choose your move:", 
            view=view
        )
    
    @commands.slash_command()
    async def number_guess(self, inter):
        """Start a number guessing game"""
        # Generate a random number between 1 and 100
        target_number = random.randint(1, 100)
        attempts = 0
        max_attempts = 7
        
        # Create a modal for guessing
        modal = disnake.ui.Modal(
            title="Number Guessing Game",
            custom_id="number_guess_modal"
        )
        
        modal.add_components(
            disnake.ui.TextInput(
                label="Your Guess",
                placeholder="Enter a number between 1 and 100",
                custom_id="guess_input",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=3
            )
        )
        
        # Keep track of game state
        self.ongoing_games[inter.author.id] = {
            "target": target_number,
            "attempts": 0,
            "max_attempts": max_attempts
        }
        
        async def modal_callback(modal_inter):
            # Retrieve game state
            game_state = self.ongoing_games.get(modal_inter.author.id)
            if not game_state:
                return await modal_inter.response.send_message(
                    "Game not found. Start a new game with /number_guess", 
                    ephemeral=True
                )
            
            try:
                guess = int(modal_inter.text_values["guess_input"])
            except ValueError:
                return await modal_inter.response.send_message(
                    "Please enter a valid number!", 
                    ephemeral=True
                )
            
            # Increment attempts
            game_state["attempts"] += 1
            
            # Check the guess
            if guess == game_state["target"]:
                await modal_inter.response.send_message(
                    f"🎉 Congratulations! You guessed the number **{guess}** in {game_state['attempts']} attempts!"
                )
                del self.ongoing_games[modal_inter.author.id]
            elif guess < game_state["target"]:
                remaining = game_state["max_attempts"] - game_state["attempts"]
                if remaining > 0:
                    await modal_inter.response.send_message(
                        f"📈 Too low! Try a higher number. {remaining} attempts left."
                    )
                else:
                    await modal_inter.response.send_message(
                        f"❌ Game over! The number was {game_state['target']}."
                    )
                    del self.ongoing_games[modal_inter.author.id]
            else:
                remaining = game_state["max_attempts"] - game_state["attempts"]
                if remaining > 0:
                    await modal_inter.response.send_message(
                        f"📉 Too high! Try a lower number. {remaining} attempts left."
                    )
                else:
                    await modal_inter.response.send_message(
                        f"❌ Game over! The number was {game_state['target']}."
                    )
                    del self.ongoing_games[modal_inter.author.id]
        
        # Set the modal's callback
        modal.callback = modal_callback
        
        # Send instructions and the modal
        await inter.response.send_modal(modal)
        await inter.followup.send(
            "I've chosen a secret number between 1 and 100. Try to guess it in 7 attempts!", 
            ephemeral=True
        )
    
    @commands.slash_command()
    async def magic8ball(
        self, 
        inter, 
        question: str = commands.Param(description="Ask the Magic 8-Ball a yes or no question")
    ):
        """Consult the mystical Magic 8-Ball"""
        responses = [
            "It is certain.",
            "Without a doubt.",
            "You may rely on it.",
            "Yes, definitely.",
            "It is decidedly so.",
            "As I see it, yes.",
            "Most likely.",
            "Yes.",
            "Outlook good.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Better not tell you now.",
            "Ask again later.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "Outlook not so good.",
            "My sources say no.",
            "Very doubtful.",
            "My reply is no."
        ]
        
        # Choose a random response
        response = random.choice(responses)
        
        # Create an embed for a more visually appealing result
        embed = disnake.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n\n**Answer:** {response}",
            color=disnake.Color.purple()
        )
        
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))