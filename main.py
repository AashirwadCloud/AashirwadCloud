import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # Required for future moderation/ticket features

bot = commands.Bot(command_prefix="!", intents=intents)

# Memory-based feature toggles (initially all OFF)
feature_toggles = {
    "Moderation": False,
    "Fun": False,
    "Tickets": False,
    "Economy": False
}

# Only allow bot owner to access dashboard
BOT_OWNER_ID = 123456789012345678  # 🔁 Replace with your actual Discord user ID

# Generate interactive dashboard view
def generate_dashboard_view():
    view = View(timeout=None)
    for feature, enabled in feature_toggles.items():
        button = Button(
            label=f"{feature} {'✅' if enabled else '❌'}",
            style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red,
            custom_id=feature
        )
        view.add_item(button)
    return view

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("🔧 Dashboard ready. Use `!dashboard` in Discord.")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

@bot.command(name="dashboard")
async def dashboard(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ You are not authorized to use this dashboard.")

    embed = discord.Embed(
        title="🛠️ Bot Feature Dashboard",
        description="Toggle features using the buttons below.",
        color=0x00ffcc
    )
    await ctx.send(embed=embed, view=generate_dashboard_view())

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    if interaction.user.id != BOT_OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can toggle features.", ephemeral=True)

    feature = interaction.data["custom_id"]
    if feature in feature_toggles:
        feature_toggles[feature] = not feature_toggles[feature]
        await interaction.response.edit_message(view=generate_dashboard_view())
        print(f"🔁 Toggled: {feature} -> {feature_toggles[feature]}")
    else:
        await interaction.response.send_message("⚠️ Unknown feature.", ephemeral=True)

# Run the bot
bot.run(os.getenv("TOKEN"))
