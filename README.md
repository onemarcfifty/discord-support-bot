# FIRSTLINE (discord-support-bot) is a discord-bot

Firstline is a fork of RALF

It can do the following things (release version 0.1):

- Help the user create a support thread with a modal view
- let everyone know that someone is asking for help

Planned: 

- provide a knowledge base / search function in older threads
- maybe unarchive threads that have not been solved yet
- scale out to provide usability across multiple guilds (i.e. allow hosted model)

## How to use

You need the discord.py wrapper from Rapptz :

    git clone https://github.com/Rapptz/discord.py
    cd discord.py/
    python3 -m pip install -U .[voice]

Next, adapt the `config.json` file to reflect your token etc.
See the explanations of the settings in the `config.py` file

Now you can cd into the bot's directory and launch it with

    python3 main.py
