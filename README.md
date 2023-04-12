# DayZ-Console-Killfeed
DayZ PVE Bot - Original creator vic#1337, Modified for PVE By Mr Relliks

# Changes
- A Live Player Count for Discord (Using Voice Channel)
- A Player Tracker for Admins using Izurvive.
- An automated Server Restart every X hours (default 12) - with ability to ping a specific role on Discord.




# Requirements
- Server for hosting (Raspberry Pi works well, Or use Linode.)
- Python 3.8+
- A brain

# Installation
Setup Discord Bot
` https://discord.com/developers/applications `

Setup Discord Channels
` Set up an admin only channel for locations, PVP and other (or make them public, idc) and a public voice channel for Live player count (dont worry what you call it, the bot renames it automatically) `

Install requirements:
`pip3 install -r requirements.txt`

Edit configuration:
`nano config.py` or open in notepad

Run the bot:
`python3 main.py`


