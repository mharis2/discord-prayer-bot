# Prayer Times Discord Bot

## Description

This repository contains the code for a Discord bot that fetches and announces Islamic prayer times for the city of Edmonton, Canada.

The bot uses the [Aladhan API](http://api.aladhan.com/v1/timingsByCity) to retrieve the prayer times, and announces each prayer time in the designated Discord channel. Additionally, it provides several commands that users can use to manually retrieve prayer times.

## Goals

The main goal of this project is to provide a convenient tool for members of a Discord server to know the prayer times without needing to leave the server or use an external tool. This can be particularly useful for online communities that organize around shared religious observances.

By maintaining this bot, I hope to support and enhance the practice of prayer for the users. I also aim to learn more about building and deploying Discord bots, and to contribute to the open-source community.

## Technologies

This project is built with Python, using the discord.py library to interact with the Discord API. It also utilizes the requests library to fetch data from the Aladhan API, and the pytz library to handle timezones.

## Future Improvements

In the future, I plan to add more features to the bot, such as the ability to customize the city and country for which prayer times are fetched, and to choose the method of calculation for the prayer times.

I also plan to add more interactivity to the bot, such as responding to user queries about the meaning and significance of the prayers.

## Contributions

While this project is primarily for personal use, I welcome any feedback, suggestions, or contributions. Please feel free to open an issue or submit a pull request.
