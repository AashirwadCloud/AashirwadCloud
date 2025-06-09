import os
import json
import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# --- Intents & Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Feature Toggle System (Part 1 + Part 2) ---
feature_toggles = {
    "Moderation": False,
    "Fun": False,
    "Tickets": True,   # Enable by default
    "Economy": False
}

BOT_OWNER_ID = 1217747285463531522  # Replace with your ID

def generate_dashboard_view():
    view = View()
    for feature, enabled in feature_toggles.items():
        button = Button(
            label=f"{feature} {'✅' if enabled else '❌'}",
            style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red,
            custom_id=f"toggle_{feature}"
        )
        view.add_item(button)
    return view

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

# --- Ticket System (Part 3) ---
CONFIG_FILE = "ticket_config.json"
TICKETS_FILE = "open_tickets.json"

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

ticket_config = load_json(CONFIG_FILE)
open_tickets = load_json(TICKETS_FILE)

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx, *, args):
    """
    Usage:
    !ticketsetup Title | Description | Button Text | Category Name | @StaffRole
    """
    try:
        title, description, button, category_name, role_mention = [x.strip() for x in args.split("|")]
    except:
        return await ctx.send("❌ Format:\n`!ticketsetup Title | Description | Button | Category | @Role`")

    staff_role = ctx.message.role_mentions[0] if ctx.message.role_mentions else None
    if not staff_role:
        return await ctx.send("❌ You must mention a staff role.")

    config = {
        "title": title,
        "description": description,
        "button": button,
        "category": category_name,
        "staff_role_id": staff_role.id
    }

    ticket_config[str(ctx.guild.id)] = config
    save_json(CONFIG_FILE, ticket_config)

    embed = discord.Embed(title=title, description=description, color=0x00ffcc)
    view = View()
    view.add_item(Button(label=button, style=discord.ButtonStyle.green, custom_id="open_ticket"))
    await ctx.send(embed=embed, view=view)
    await ctx.send("✅ Ticket system setup complete.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def add(ctx, member: discord.Member):
    if "ticket" not in ctx.channel.name:
        return await ctx.send("❌ This is not a ticket channel.")
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"✅ {member.mention} added to the ticket.")

@bot.command()
async def close(ctx):
    if "ticket" not in ctx.channel.name:
        return await ctx.send("❌ This is not a ticket channel.")
    await ctx.send("🕐 Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    for key, cid in list(open_tickets.items()):
        if cid == ctx.channel.id:
            del open_tickets[key]
            save_json(TICKETS_FILE, open_tickets)
            break
    await ctx.channel.delete()

# --- Interaction Handler ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    cid = interaction.data.get("custom_id")

    # Toggle buttons
    if cid and cid.startswith("toggle_") and interaction.user.id == BOT_OWNER_ID:
        feature = cid.replace("toggle_", "")
        if feature in feature_toggles:
            feature_toggles[feature] = not feature_toggles[feature]
            await interaction.response.edit_message(view=generate_dashboard_view())
            print(f"Toggled: {feature} -> {feature_toggles[feature]}")
        return

    # Ticket button
    if cid == "open_ticket":
        user = interaction.user
        guild = interaction.guild
        gid = str(guild.id)
        uid = str(user.id)

        if gid not in ticket_config:
            return await interaction.response.send_message("❌ Ticket system not configured.", ephemeral=True)

        if f"{gid}-{uid}" in open_tickets:
            ticket_id = open_tickets[f"{gid}-{uid}"]
            channel = guild.get_channel(ticket_id)
            if channel:
                return await interaction.response.send_message(f"📨 You already have a ticket: {channel.mention}", ephemeral=True)

        config = ticket_config[gid]
        category = discord.utils.get(guild.categories, name=config["category"])
        if not category:
            category = await guild.create_category(config["category"])

        staff_role = guild.get_role(config["staff_role_id"])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}".replace(" ", "-"),
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {user.name}"
        )

        open_tickets[f"{gid}-{uid}"] = channel.id
        save_json(TICKETS_FILE, open_tickets)

        await channel.send(f"🎫 {user.mention}, thank you for opening a ticket! A team member will be with you shortly.\nUse `!close` to close this ticket.")
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# --- Bot Ready ---
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")

# --- Start Bot ---
bot.run(os.getenv("TOKEN"))
