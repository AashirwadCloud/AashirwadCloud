import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True       # Needed if your bot reads messages
intents.members = True               # Needed if using member join/leave
intents.presences = False            # Optional

bot = commands.Bot(command_prefix="!", intents=intents)
import os
bot.run(os.getenv("TOKEN"))
