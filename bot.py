import discord
from discord.ext import tasks, commands
import requests
import datetime
import os
from dotenv import load_dotenv
from pytz import timezone
import pytz
import asyncio
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    get_prayer_times.start()

async def fetch_prayer_times():
    city = "Edmonton"
    country = "Canada"
    
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}"
    response = requests.get(url)
    data = response.json()
    return data['data']['timings']

@tasks.loop(hours=24)
async def get_prayer_times():
    timings = await fetch_prayer_times()

    tz = timezone('America/Edmonton')
    current_date = datetime.date.today()

    for prayer, time in timings.items():
        if prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            prayer_time = datetime.datetime.strptime(time, "%H:%M")
            prayer_time = prayer_time.replace(year=current_date.year, month=current_date.month, day=current_date.day)

            prayer_time = tz.localize(prayer_time)
            # print(f"Prayer time for {prayer} is {prayer_time}")

            if prayer_time > datetime.datetime.now(tz):
                delay = (prayer_time - datetime.datetime.now(tz)).total_seconds()

                # print(f"Scheduling {prayer} prayer for {prayer_time}") # debug print statement
                # print(f"Delay for {prayer} prayer is {delay} seconds") # debug print statement

                bot.loop.call_later(delay, schedule_announcement, prayer)

def schedule_announcement(prayer):
    bot.loop.create_task(announce_prayer(prayer))

@bot.command(name='test_schedule')
async def test_schedule_command(ctx):
    await get_prayer_times()

@bot.command()
async def announce_prayer(prayer):
    channel = bot.get_channel(CHANNEL_ID)

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
async def prayer(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid prayer command passed...')

@prayer.command(name='help')
async def prayer_help_command(ctx):
    help_message = """
**General Commands**:
- `!prayer time all` - Shows the times for all prayers today.
- `!prayer time [prayer]` - Shows the time for a specific prayer. Replace `[prayer]` with Fajr, Dhuhr, Asr, Maghrib, or Isha.

**Debugging Commands** (for testing and debugging purposes):
- `!test_schedule` - Triggers a call to the `get_prayer_times` function immediately.
- `!test_announcement [prayer]` - Sends a test announcement for the specified prayer. Replace `[prayer]` with Fajr, Dhuhr, Asr, Maghrib, or Isha.
- `!time_debug` - Displays the current time in Edmonton.
    """
    await ctx.send(help_message)


@prayer.command(name='time')
async def prayer_time_command(ctx, type="all"):
    timings = await fetch_prayer_times()

    if type.lower() != "all" and type not in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
        await ctx.send(f'Invalid prayer type: {type}')
        return

    times_str = ""
    for prayer, time in timings.items():
        if prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'] and (type.lower() == "all" or type.lower() == prayer.lower()):
            times_str += f"{prayer}: {time}\n"

    if not times_str:
        times_str = f"No times found for prayer: {type}"
    
    await ctx.send(times_str)

@bot.command(name='test_announcement')
async def test_announcement_command(ctx, prayer):
    await announce_prayer(prayer)

@bot.command(name='time_debug')
async def time_debug_command(ctx):
    tz = pytz.timezone('America/Edmonton')
    current_time = datetime.datetime.now(tz)
    await ctx.send(f'Current time in Edmonton: {current_time}')

bot.run(TOKEN)
