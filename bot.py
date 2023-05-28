import discord
from discord.ext import tasks, commands
import datetime
import os
from dotenv import load_dotenv
from pytz import timezone
import pytz
import sqlite3
import aiohttp
import time
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

server_configs = {}  # Add this line
db = sqlite3.connect('server_configs.db')  

@bot.event
async def on_ready():
    if not get_prayer_times.is_running():
        get_prayer_times.start()  # Start the prayer time loop only if it is not already running
    for guild in bot.guilds:
        cur = db.cursor()
        cur.execute(f"SELECT * FROM server_configs WHERE guild_id = {guild.id}")
        settings = cur.fetchone()
        if settings is not None:
            # The result will be a tuple. We need to convert it to a dictionary.
            server_configs[guild.id] = {
                'guild_id': settings[0],
                'channel_id': settings[1],
                'city': settings[2],
                'country': settings[3],
                'timezone': settings[4]
            }

    print("Loaded server configs:")
    for server_id, config in server_configs.items():
        server_name = bot.get_guild(server_id).name
        print(f"Server {server_name} ({server_id}):")
        print(f"    Channel ID: {config['channel_id']}")
        print(f"    City: {config['city']}")
        print(f"    Country: {config['country']}")
        print(f"    Timezone: {config['timezone']}")





def get_db_connection():
    conn = sqlite3.connect('server_configs.db')
    return conn


@bot.event
async def on_guild_join(guild):
    default_channel = None
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            default_channel = channel
            break

    if default_channel is not None:
        await default_channel.send(
            "السلام عليكم ورحمة الله وبركاته \n\n"
            "To setup me in this server, you need to specify the #channel-name, city, country and timezone.\n"
            "For example, you can type: \n\n"
            "`!salah setup #general Edmonton Canada America/Edmonton`\n\n"
            "For more, try: `!salah help`.\n\n"
            "And don't forget, the timezone must be provided in a format recognized by the pytz library (e.g., 'America/Edmonton').\n\n"
            "بسم الله الرحمن الرحيم "
        )

    # Fetch server config for the new guild and add to the in-memory dictionary
    cur = db.cursor()
    cur.execute(f"SELECT * FROM server_configs WHERE guild_id = {guild.id}")
    settings = cur.fetchone()
    if settings is not None:
        # The result will be a tuple. We need to convert it to a dictionary.
        server_configs[guild.id] = {
            'guild_id': settings[0],
            'channel_id': settings[1],
            'city': settings[2],
            'country': settings[3],
            'timezone': settings[4]
        }


async def fetch_prayer_times(city, country):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                data = await response.json()
                return data['data']['timings']
        except Exception as e:
            print(f"Unable to connect to the API to fetch prayer times for {city}, {country}. Error: {e}")

@tasks.loop(hours=24)
async def get_prayer_times():
    for guild in bot.guilds:
        try:
            # Get the server-specific configuration
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT channel_id, city, country, timezone 
                FROM server_configs 
                WHERE guild_id = ?
            """, (guild.id,))

            config = cur.fetchone()

            conn.close()

            if config is None:
                print(f"No config found for guild {guild.name}. Skipping...")
                continue

            channel_id, city, country, tz_str = config
            tz = timezone(tz_str)

            timings = await fetch_prayer_times(city, country)
            current_date = datetime.date.today()

            for prayer, time in timings.items():
                if prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                    prayer_time = datetime.datetime.strptime(time, "%H:%M")
                    prayer_time = prayer_time.replace(year=current_date.year, month=current_date.month, day=current_date.day)
                    prayer_time = tz.localize(prayer_time)

                    if prayer_time > datetime.datetime.now(tz):
                        delay = (prayer_time - datetime.datetime.now(tz)).total_seconds()
                        bot.loop.call_later(delay, bot.loop.create_task, announce_prayer(prayer, channel_id))
        except Exception as e:
            print(f"An error occurred while fetching prayer times for guild {guild.name}: {e}")




def schedule_announcement(prayer, channel_id):
    bot.loop.create_task(announce_prayer(prayer, channel_id))

@bot.command()
async def announce_prayer(prayer, channel_id):
    channel = bot.get_channel(int(channel_id))  # Convert channel_id to int

    hadith = (
        "**Abdullah ibn Mas’ud reported:\n\n**I said, “O Messenger of Allah, which deeds are best?”\n\n"
        "The Messenger of Allah, peace and blessings be upon him, said, “**Prayer on time.**”\n\n"
        "I said, “Then what, O Messenger of Allah?” The Prophet said, “**Good treatment of your parents.**”\n\n"
        "I said, “Then what, O Messenger of Allah?” The Prophet said, “**That people are safe from your tongue.**”\n\n"
        "**Source**: al-Mu’jam al-Kabīr 9687\n"
        "**Grade**: **Sahih** (authentic) according to **Al-Albani**"
    )

    await channel.send(f"It's time for **{prayer}** prayer.\n\n{hadith}")

@bot.group(invoke_without_command=True)
async def salah(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid salah command passed...')

@salah.command(name='help')
async def salah_help_command(ctx):
    help_message = """
**General Commands**:
- `!salah times` - Shows the times for all prayers today for the default city and country.
- `!salah times [city] [country]` - Shows the times for all prayers today for the specified city and country.
- `!salah times [city] [country] [prayer]` - Shows the time for a specific prayer for the specified city and country. Replace `[prayer]` with Fajr, Dhuhr, Asr, Maghrib, or Isha.

**Setup Commands**:
- `!salah setup` - Sets up the bot on your server. You need to provide the following information as arguments: channel ID, city, country, and timezone. 
  Example: `!salah setup #general Calgary Canada MST`
- `!salah setup_modify` - Modifies the setup of the bot on your server. This command also requires the channel ID, city, country, and timezone as arguments.
  Example: `!salah setup modify #announcements Toronto Canada EST`

**Debugging Commands** (for testing and debugging purposes):
- `!test_schedule` - Triggers a call to the `get_prayer_times` function immediately.
- `!test_announcement [prayer]` - Sends a test announcement for the specified prayer. Replace `[prayer]` with Fajr, Dhuhr, Asr, Maghrib, or Isha.
- `!time_debug` - Displays the current time in Edmonton.
    """
    await ctx.send(help_message)

    
@bot.command(name='test_schedule')
async def test_schedule_command(ctx):
    await get_prayer_times()


@salah.command(name='times')
async def salah_time_command(ctx, *args):
    city = None
    country = None
    type = "all"

    # Check if city and country are provided
    if len(args) == 2:
        city, country = args
    elif len(args) == 3:
        city, country, type = args
    else:
        # Get the server configuration
        config = server_configs.get(ctx.guild.id)
        if config is None:
            await ctx.send("Bot has not been set up on this server.")
            return
        city = config['city']
        country = config['country']

    # Fetch the prayer times
    timings = await fetch_prayer_times(city, country)

    if timings is None:
        await ctx.send(f"Sorry, I couldn't fetch prayer times for {city}, {country}. The service might be temporarily unavailable. Please try again later.")
        return

    if type.lower() != "all" and type not in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
        await ctx.send(f'Invalid prayer type: {type}')
        return

    if type.lower() == "all":
        # Define the desired order of prayer times
        ordered_prayers =  ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']

        # Update the name for the last third of the night
        if 'Lastthird' in timings:
            timings['Last Third of The Night'] = timings.pop('Lastthird')

        # Construct the message with the prayer times in the desired order
        message = f"Current prayer timetable for **{city}, {country}**:\n\n"
        for prayer in ordered_prayers:
            if prayer in timings:
                message += f"**{prayer}**: {timings[prayer]}\n"
    else:
        time = timings.get(type) 
        message = f"Salah time for **{type}** in **{city}, {country}**: {time}"

    await ctx.send(message)




@bot.command(name='test_announcement')
async def test_announcement_command(ctx, prayer_name):
    guild_id = ctx.guild.id
    if guild_id not in server_configs:
        await ctx.send("This server has not been set up yet. Please run the !setup command.")
        return

    channel_id = server_configs[guild_id]['channel_id']
    await announce_prayer(prayer_name, channel_id)  # Reverse the order of arguments here


@bot.command(name='time_debug')
async def time_debug_command(ctx):
    tz = pytz.timezone('America/Edmonton')
    current_time = datetime.datetime.now(tz)
    await ctx.send(f'Current time in Edmonton: {current_time}')


@bot.event
async def on_guild_remove(guild):
    # Get a cursor
    cur = db.cursor()
    
    # Delete the row corresponding to the guild from which the bot was removed
    cur.execute("DELETE FROM server_configs WHERE guild_id = ?", (guild.id,))
    db.commit()
    
    # Remove the config from the in-memory dictionary
    if guild.id in server_configs:
        del server_configs[guild.id]

    print(f"Deleted server config for guild {guild.id}")


@salah.command(name='setup')
async def salah_setup_command(ctx, channel: discord.TextChannel = None, city: str = None, country: str = None, timezone: str = None):
    # Check for missing parameters
    if channel is None or city is None or country is None or timezone is None:
        await ctx.send(
            "Missing parameters! Please provide a channel, city, country, and timezone in the format: "
            "`!salah setup #channel [city] [country] [timezone]`\n\n"
            "For example: `!salah setup #general Edmonton Canada America/Edmonton`"
        )
        return

    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        await ctx.send(f"Invalid timezone: {timezone}\nMake sure the timezone is recognized by the pytz library (e.g., 'America/Edmonton').")
        return

    await ctx.send("Setting up the bot for this server...")

    # Get a cursor
    cur = db.cursor()

    # Check if there are existing settings for this server
    cur.execute("SELECT * FROM server_configs WHERE guild_id = ?", (ctx.guild.id,))
    existing_settings = cur.fetchone()

    # If there are existing settings for this server, update them
    if existing_settings is not None:
        cur.execute("""
            UPDATE server_configs
            SET channel_id = ?,
                city = ?,
                country = ?,
                timezone = ?
            WHERE guild_id = ?
        """, (channel.id, city, country, timezone, ctx.guild.id))

    # If there are no existing settings for this server, insert new ones
    else:
        cur.execute("""
            INSERT INTO server_configs (guild_id, channel_id, city, country, timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (ctx.guild.id, channel.id, city, country, timezone))

    db.commit()

    server_configs[ctx.guild.id] = {
        'channel_id': channel.id,
        'city': city,
        'country': country,
        'timezone': timezone,
    }

    await ctx.send("Bot has been set up successfully!")


@salah.command(name='setup_modify')
async def salah_setup_modify_command(ctx, channel: discord.TextChannel = None, city: str = None, country: str = None, timezone: str = None):
    # Check for missing parameters
    if channel is None or city is None or country is None or timezone is None:
        await ctx.send(
            "Missing parameters! Please provide a channel, city, country, and timezone in the format: "
            "`!salah setup_modify #channel [city] [country] [timezone]`\n\n"
            "For example: `!salah setup_modify #announcements Edmonton Canada America/Edmonton`"
        )
        return

    # Check if setup exists for the guild
    if ctx.guild.id not in server_configs:
        await ctx.send(
            "No setup exists for this server. Please use `!salah setup [city] [country] [timezone]` to create one."
        )
        return

    # Update the server configuration in the database
    cur = db.cursor()
    cur.execute(
        f"UPDATE server_configs SET city = ?, country = ?, timezone = ? WHERE guild_id = ?",
        (city, country, timezone, ctx.guild.id)
    )
    db.commit()

    # Update the server configuration in memory
    server_configs[ctx.guild.id]['city'] = city
    server_configs[ctx.guild.id]['country'] = country
    server_configs[ctx.guild.id]['timezone'] = timezone

    await ctx.send(f"Bot setup has been modified successfully for {city}, {country} with timezone {timezone}!")

def get_server_config(guild_id):
    return server_configs.get(guild_id)



 
bot.run(TOKEN)