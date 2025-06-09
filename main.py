import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Toggle states (initially off)
feature_toggles = {
    "Moderation": False,
    "Fun": False,
    "Tickets": False,
    "Economy": False
}

BOT_OWNER_ID = 1217747285463531522  # Replace this

# Generate dashboard buttons
def generate_dashboard_view():
    view = View()
    for feature, enabled in feature_toggles.items():
        button = Button(
            label=f"{feature} {'✅' if enabled else '❌'}",
            style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red,
            custom_id=feature
        )
        view.add_item(button)
    return view

# Bot ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Dashboard command
@bot.command()
async def dashboard(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ You are not authorized to use this dashboard.")
    
    embed = discord.Embed(
        title="🛠️ Bot Feature Dashboard",
        description="Toggle features using the buttons below.",
        color=0x00ffcc
    )
    await ctx.send(embed=embed, view=generate_dashboard_view())

# Handle button interactions
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
        print(f"Toggled: {feature} -> {feature_toggles[feature]}")

# Moderation Commands
@bot.command()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not feature_toggles["Moderation"]:
        return await ctx.send("⚠️ Moderation module is disabled.")
    if not ctx.author.guild_permissions.kick_members:
        return await ctx.send("❌ You do not have permission to kick members.")
    await member.kick(reason=reason)
    await ctx.send(f"✅ Kicked {member.mention} | Reason: {reason}")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not feature_toggles["Moderation"]:
        return await ctx.send("⚠️ Moderation module is disabled.")
    if not ctx.author.guild_permissions.ban_members:
        return await ctx.send("❌ You do not have permission to ban members.")
    await member.ban(reason=reason)
    await ctx.send(f"✅ Banned {member.mention} | Reason: {reason}")

@bot.command()
async def mute(ctx, member: discord.Member):
    if not feature_toggles["Moderation"]:
        return await ctx.send("⚠️ Moderation module is disabled.")
    if not ctx.author.guild_permissions.manage_roles:
        return await ctx.send("❌ You do not have permission to mute members.")

    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted", reason="Mute role for bot")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False, add_reactions=False)

    await member.add_roles(mute_role)
    await ctx.send(f"🔇 {member.mention} has been muted.")

# Ticket System
@bot.command()
async def ticket(ctx):
    if not feature_toggles["Tickets"]:
        return await ctx.send("🎫 Ticket system is currently disabled.")
    
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel_name = f"ticket-{ctx.author.name}".replace(" ", "-").lower()
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        return await ctx.send(f"📝 You already have a ticket: {existing.mention}")

    ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, reason="New support ticket")
    await ticket_channel.send(f"🎟️ Hello {ctx.author.mention}, staff will be with you shortly.")
    await ctx.send(f"✅ Ticket created: {ticket_channel.mention}")

@bot.command()
async def close(ctx):
    if "ticket" not in ctx.channel.name:
        return await ctx.send("❌ This is not a ticket channel.")
    await ctx.send("🛑 Closing ticket in 3 seconds...")
    await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=3))
    await ctx.channel.delete()

# Run bot
bot.run(os.getenv("TOKEN"))
