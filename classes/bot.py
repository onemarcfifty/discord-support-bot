import discord
from sys import exit
from discord import app_commands
from classes.support import Support


# #######################################
# The OMFClient class
# #######################################


class FirstLineClient(discord.Client):

    asked_question = False
    last_question: discord.Message = None
    lastNotifyTimeStamp = None

    # #######################################
    # init constructor
    # #######################################

    def __init__(self) -> None:

        print('Init')
        
        # Try to set all intents

        intents = discord.Intents.all()
        super().__init__(intents=intents)

        # We need a `discord.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)

        self.tree = app_commands.CommandTree(self)

        # The support command will ask for a thread title and description
        # and create a support thread for us

        @self.tree.command(name="support", description="Create a support thread")
        async def support(interaction: discord.Interaction):
            x : Support
            x= Support()
            await interaction.response.send_modal(x)

    # #########################
    # setup_hook waits for the
    # command tree to sync
    # #########################

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        await self.tree.sync()


    # ######################################################
    # on_ready is called once the client is initialized
    # ######################################################

    async def on_ready(self):
        print('Logged on as', self.user)

    # ######################################################
    # on_message scans for message contents and takes 
    # corresponding actions.
    # User sends ping - bot replies with pong
    # User asks a question - bot checks if question has been 
    # answered
    # ######################################################

    async def on_message(self, message  : discord.Message ):
        print("{} has just sent {}".format(message.author, message.content))

        # don't respond to ourselves
        if message.author == self.user:
            return

        # reset the idle timer if a message has been sent or received
        self.channel_idle_timer = 0

        # check if there is a question 
        if "?" in message.content:
            self.asked_question = True
            self.last_question = message
        else:
            self.asked_question = False
            self.last_question = None

    # ######################################################
    # on_typing detects if a user types. 
    # We might use this one day to have users agree to policies etc.
    # before they are allowed to speak
    # or we might launch the Support() Modal if a user starts
    # to type in the support channel
    # ######################################################

    async def on_typing(self, channel, user, _):
        # we do not want the bot to reply to itself
        if user.id == self.user.id:
            return
        print(f"{user} is typing in {channel}")
        self.channel_idle_timer = 0
        #await channel.trigger_typing()
