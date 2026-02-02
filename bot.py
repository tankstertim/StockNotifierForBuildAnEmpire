import discord
from discord.ext import commands, tasks
from discord import Role, app_commands
from dotenv import load_dotenv
from stocks import get_all_stocks
from stockview import StockView
from constants import *
from datetime import datetime, timedelta
import json
import asyncio
import os 

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

current_stock = {}
item_choices= [app_commands.Choice(name=i, value=i) for i in ECONOMY_ITEMS + POPULATION_ITEMS + UTILITY_ITEMS]

channel_lock = asyncio.Lock()
roles_lock = asyncio.Lock()
trackers_lock = asyncio.Lock()

async def save_tracker(user_id, item):
    async with trackers_lock:
        trackers = {}
        with open("trackers.json", "r") as f:
            trackers = json.load(f)
        
        if not item in trackers:
            trackers[item] = []
        
        if not str(user_id) in trackers[item]:
            trackers[item].append(str(user_id))
        
        with open("trackers.json", "w") as f:
            json.dump(trackers, f)

async def remove_tracker(user_id, item):
    async with trackers_lock:
        trackers = {}
        with open("trackers.json", "r") as f:
            trackers = json.load(f)
        
        if not item in trackers:
            trackers[item] = []
        
        if str(user_id) in trackers[item]:
            trackers[item].remove(str(user_id))
        
        with open("trackers.json", "w") as f:
            json.dump(trackers, f)

async def get_trackers(item):
    async with trackers_lock:
        with open("trackers.json", "r") as f:
            trackers = json.load(f)

        return trackers.get(item, [])
        
async def save_channel(guild_id,channel_id):
    async with channel_lock:
        channels= {}
        with open("channels.json", "r") as f:
            channels = json.load(f)
        
        channels[str(guild_id)] = channel_id
        with open("channels.json", "w") as f:
            json.dump(channels, f)

async def get_channel(guild_id):
    async with channel_lock:
        with open("channels.json", "r") as f:
            channels = json.load(f)
        return channels.get(str(guild_id), None)

async def save_notify_role(guild_id, role_id, item):
    # implement role notification storage
    async with roles_lock:
        notify_roles = {}
        with open("notify_roles.json", "r") as f:
            notify_roles = json.load(f) 
        if str(guild_id) not in notify_roles:
            notify_roles[str(guild_id)] = {}
        
        notify_roles[str(guild_id)][item] = role_id
        with open("notify_roles.json", "w") as f:
            json.dump(notify_roles, f)
   
async def remove_notify_role(guild_id, item):
    async with roles_lock:
        notify_roles = {}
        with open("notify_roles.json", "r") as f:
            notify_roles = json.load(f) 
        if str(guild_id) in notify_roles and item in notify_roles[str(guild_id)]:
            del notify_roles[str(guild_id)][item]
        
        with open("notify_roles.json", "w") as f:
            json.dump(notify_roles, f)


async def get_roles_to_notify(guild_id, items):
    async with roles_lock:
        with open("notify_roles.json", "r") as f:
            notify_roles = json.load(f)
        roles = []

        for item in items:
            guild_roles = notify_roles.get(str(guild_id), {})
            role_id = guild_roles.get(item, None)
            if role_id:
                roles.append(role_id)
        return roles

def get_stock_embed(data):  # your function returning the stock dict
    # Full stock embed (all categories)
    embed = discord.Embed(
        title="🛒 Shop Stock(USE PRIVATE SERVER TO GET ACCURATE STOCK)",
        description="See what items are in stock!",
        color=0x57F287
    )
    IN_STOCK = "✅"
    OUT_STOCK = "❌"
    for category, items in data.items():
        lines = []
        for name, in_stock in items.items():
            if not in_stock:
                continue
            icon = IN_STOCK if in_stock else OUT_STOCK
            lines.append(f"**{name.title()}** {icon}")
        embed.add_field(name=f"📦 {category.title()}", value="\n".join(lines), inline=False)

    return embed

   
    
bot = commands.Bot(command_prefix="!", intents=intents)  


@tasks.loop(seconds=300)
async def send_stock():
    global current_stock
    await asyncio.sleep(5)
    data = get_all_stocks()
    current_stock = data
    items_to_notify = ["restock"]
    for category, items in data.items():
        for item, stock in items.items():
            if stock:
                items_to_notify.append(item)
    

   
           
    embed = get_stock_embed(data)

    for guild in bot.guilds:
        channel_id = await get_channel(guild.id)
        if channel_id is None:
            continue
        channel = bot.get_channel(channel_id)
        if channel is None:
            continue
        roles_to_notify = await get_roles_to_notify(guild.id, items_to_notify)
        role_mentions = ' '.join(f"<@&{role_id}>" for role_id in roles_to_notify)
        try:
            if role_mentions != "":
                await channel.send(role_mentions)
            
            await channel.send(embed=embed)
        except:
            continue
    
    for item in items_to_notify:
        user_ids = await get_trackers(item)
        if not user_ids or user_ids == []:
            continue
        for user_id in user_ids:
            user = None
            try:
                user = await bot.fetch_user(int(user_id))
            except:
                continue

            try:
                await user.send(f"{user.mention} 🔔 **{item}** is in stock! **USE PRIVATE SERVER TO GET ACCURATE STOCK!**")
            except Exception as e:
                print(f"Failed to send notification for {item} to {user.name}: {e}")
                continue


def has_manage_or_admin(interaction: discord.Interaction):
    
    perms = interaction.user.guild_permissions
    return True

@bot.tree.command(name="setchannel", description="set the channel to send notifications")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not has_manage_or_admin(interaction):
        await interaction.response.send_message("❌ You must have Manage Roles or Admin permissions to use this.", ephemeral=True)
        return

    await save_channel(interaction.guild.id, channel.id)
    await interaction.response.send_message(f"✅ Channel set to {channel.mention}", ephemeral=True)



@bot.tree.command(name="help", description="How notifications & servers work")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Stock Notifier Help",
        color=0x5865F2
    )

    embed.add_field(
        name="🔔 Notifications",
        value=(
            "`/notify item` → DM when item is in stock\n"
            "`/unnotify item` → stop notifications\n"
        ),
        inline=False
    )

    embed.add_field(
        name="⚠️ Use Private Servers ",
        value=(
            "Public servers are often older servers.\n"
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stock", description="shows the current stock")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def send_stock_user(interaction: discord.Interaction):
    global current_stock
    if current_stock == {}:
        return await interaction.response.send_message("The stock is not available please try again in a few minutes.", ephemeral=True)
 
    embed = get_stock_embed(current_stock)
    return await interaction.response.send_message(embed=embed)

@bot.tree.command(name="notify", description="sends you a notification when an item is in stock!")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def track_item(interaction: discord.Interaction, item: str):
    all_items = ECONOMY_ITEMS + POPULATION_ITEMS + UTILITY_ITEMS + ["restock"]
    if not item in all_items:
        return await interaction.response.send_message(f"Invalid item! Please try again.")
    await save_tracker(interaction.user.id, item)
    await interaction.response.send_message(f"🔔 you will now receive notifications for {item}.")


@bot.tree.command(name="unnotify", description="sends you a notification when an item is in stock!")
@app_commands.allowed_contexts(guilds=True,dms=True,private_channels=True)
@app_commands.user_install()
async def untrack_item(interaction: discord.Interaction, item: str):
    all_items = ECONOMY_ITEMS + POPULATION_ITEMS + UTILITY_ITEMS + ["restock"]
    if not item in all_items:
       return await interaction.response.send_message(f"Invalid item! Please try again.")
    await remove_tracker(interaction.user.id, item)
    await interaction.response.send_message(f"🔔 you will now not receive notifications for {item}.")


@bot.tree.command(name="addnotifyrole", description="add a role to notify when an item is in stock")
async def add_notify_role(interaction: discord.Interaction, role: discord.Role, item: str):
    all_items = ECONOMY_ITEMS + POPULATION_ITEMS + UTILITY_ITEMS + ["restock"]
    if not item in all_items:
        return await interaction.response.send_message(f"Invalid item! Please try again.")
        
    if not has_manage_or_admin(interaction):
        await interaction.response.send_message("❌ You must have Manage Roles or Admin permissions to use this.", ephemeral=True)
        return

    await save_notify_role(interaction.guild.id, role.id, item)
    await interaction.response.send_message(f"✅ Role {role.name} added to notifications", ephemeral=True)


@add_notify_role.autocomplete("item")
@track_item.autocomplete("item")
@untrack_item.autocomplete("item")
async def item_autocomplete(interaction: discord.Interaction, current: str):
    all_items = ECONOMY_ITEMS + POPULATION_ITEMS + UTILITY_ITEMS + ["restock"]
    return [
        app_commands.Choice(name=item, value=item)
        for item in all_items
        if current.lower() in item.lower()

    ][:25]  # limit to 25 choices


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready {bot.user.name}")
    for guild in bot.guilds:
            print(guild.name)
    now = datetime.now()
    # Next minute divisible by 5
    next_run_minute = (now.minute // 5 + 1) * 5
    if next_run_minute >= 60:
        next_run_minute -= 60
        next_run_hour = now.hour + 1
    else:
        next_run_hour = now.hour

    if next_run_hour == 24:
        next_run_hour = 0
    next_run = now.replace(hour=next_run_hour, minute=next_run_minute, second=0, microsecond=0)
    delta = (next_run - now).total_seconds()

    delta += 73

    print(f"Waiting {delta:.2f} seconds until first synchronized stock update...")
    await asyncio.sleep(delta)
    send_stock.start()

bot.run(TOKEN)