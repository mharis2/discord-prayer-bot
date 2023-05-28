from bot import PrayerBot
import discord
def main():
    bot = PrayerBot(command_prefix='!', intents=discord.Intents.all())
    bot.run()

if __name__ == "__main__":
    main()