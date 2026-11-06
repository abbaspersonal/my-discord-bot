import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from keep_alive import keep_alive

# Setup bot intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 1. WELCOME & LEAVE MESSAGES ---
@bot.event
async def on_member_join(member):
    # Aapke server me "welcome" naam ka channel hona chahiye
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        embed = discord.Embed(
            title=f"Welcome to the server, {member.name}! 🎉",
            description="We are glad to have you here. Check out the rules channel!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    # Aapke server me "leave" naam ka channel hona chahiye
    channel = discord.utils.get(member.guild.text_channels, name="leave")
    if channel:
        await channel.send(f"😢 **{member.name}** has left the server.")

# --- 2. AUTO-REPLY / BASIC CHAT ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower()
    if msg in ["hello", "hi", "hey"]:
        await message.reply(f"Hello {message.author.mention}! How can I help you today?")
    
    if msg in ["ip", "server ip"]:
        await message.reply("🎮 Our server IP is: `your.server.ip` \nPort: `12345`")

    await bot.process_commands(message)

# --- 3. TICKET SYSTEM WITH BUTTONS ---
class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent button

    @discord.ui.button(label="📩 Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        # Check if ticket channel already exists
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message("You already have an open ticket!", ephemeral=True)
            return

        # Setup permissions for the ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Create the ticket text channel
        ticket_channel = await guild.create_text_channel(name=f"ticket-{member.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="Ticket Support",
            description=f"Hello {member.mention}, staff will be with you shortly. Click below to close this ticket.",
            color=discord.Color.blue()
        )
        await ticket_channel.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"Ticket created! Head over to {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=ButtonStyle=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing this channel in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- 4. SLASH COMMANDS (MODERATION & SETUP) ---
@bot.tree.command(name="setup_tickets", description="Spawns the ticket creation message.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Need Support?",
        description="Click the button below to open a private support ticket with the staff team.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message("Ticket panel deployed.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=TicketCreateView())

@bot.tree.command(name="kick", description="Kicks a member from the server.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"🚫 Kicked {member.mention} for: {reason}")

# --- BOT STARTUP ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.add_view(TicketCreateView())
    bot.add_view(TicketCloseView())
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(e)

# Web server run karein aur bot ko start karein
keep_alive()
bot.run(os.environ['TOKEN'])
