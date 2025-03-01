# brian-discord-bot/cogs/fun.py

import disnake
from disnake.ext import commands
import random


class Fun(commands.Cog):
    """Fun and entertaining commands to spice up your server"""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def coinflip(self, inter):
        """Flip a coin and see heads or tails!"""
        result = random.choice(["Heads 🪙", "Tails 🪙"])

        # Create embed directly
        embed = disnake.Embed(
            title="🎲 Coin Flip",
            description=f"The coin landed on: **{result}**!",
            color=disnake.Color.blue()
        )

        await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def roll(
        self,
        inter,
        sides: int = commands.Param(
            description="Number of sides on the die", default=6, ge=2, le=100)
    ):
        """Roll a die with a specified number of sides"""
        roll_result = random.randint(1, sides)

        # Create embed directly
        embed = disnake.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a {sides}-sided die and got: **{roll_result}**!",
            color=disnake.Color.green()
        )

        await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def magic8ball(
        self,
        inter,
        question: str = commands.Param(
            description="Ask the Magic 8-Ball a yes or no question")
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

        # Create embed directly
        embed = disnake.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n\n**Answer:** {response}",
            color=disnake.Color.purple()
        )

        await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def rps(self, inter):
        """Play Rock, Paper, Scissors against the bot"""
        # Custom view for Rock, Paper, Scissors
        class RPSView(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=180.0)

                # Buttons created directly in the view
                for label, emoji in [
                    ("Rock", "🪨"),
                    ("Paper", "📄"),
                    ("Scissors", "✂️")
                ]:
                    button = disnake.ui.Button(
                        label=label,
                        style=disnake.ButtonStyle.primary,
                        emoji=emoji
                    )

                    # Create a closure around the choice
                    button.callback = self.create_callback(label)
                    self.add_item(button)

            def create_callback(self, choice):
                async def callback(button_inter):
                    # Bot's choice
                    bot_choices = ["Rock", "Paper", "Scissors"]
                    bot_choice = random.choice(bot_choices)

                    # Determine winner
                    result_map = {
                        "Rock": {
                            "Rock": "It's a tie!",
                            "Paper": "You lose! Paper covers Rock.",
                            "Scissors": "You win! Rock breaks Scissors."
                        },
                        "Paper": {
                            "Rock": "You win! Paper covers Rock.",
                            "Paper": "It's a tie!",
                            "Scissors": "You lose! Scissors cut Paper."
                        },
                        "Scissors": {
                            "Rock": "You lose! Rock breaks Scissors.",
                            "Paper": "You win! Scissors cut Paper.",
                            "Scissors": "It's a tie!"
                        }
                    }

                    result = result_map[choice][bot_choice]

                    # Create embed directly
                    embed = disnake.Embed(
                        title="Rock, Paper, Scissors",
                        description=f"**You chose {choice}**\n**I chose {bot_choice}**\n\n{result}",
                        color=disnake.Color.blue()
                    )

                    await button_inter.response.edit_message(embed=embed, view=None)

                return callback

        # Create an initial embed
        embed = disnake.Embed(
            title="🤚 Rock, Paper, Scissors",
            description="Choose your move by clicking a button below!",
            color=disnake.Color.blurple()
        )

        # Send the message with the view
        await inter.response.send_message(
            embed=embed,
            view=RPSView()
        )


def setup(bot):
    bot.add_cog(Fun(bot))
