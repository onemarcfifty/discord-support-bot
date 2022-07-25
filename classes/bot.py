#bot = Bot(
#    command_prefix=config["prefix"], prefix=config["prefix"],
#    owner_ids=config["owners"], command_attrs=dict(hidden=True), help_command=HelpFormat(),
#    allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False),
#    intents=discord.Intents(  # kwargs found at https://docs.pycord.dev/en/master/api.html?highlight=discord%20intents#discord.Intents
#        guilds=True, members=True, messages=True, reactions=True, presences=True, message_content=True,
#    )
#)



import os
import discord
from sys import exit
from discord import Client, Guild, app_commands
from classes.support import Support
from discord.ext import tasks
from classes.config import Config
import os
from discord.ext.commands import AutoShardedBot

# #######################################
# The OMFClient class
# #######################################


class FirstLineClient(AutoShardedBot):

    last_question = {}
    configData:Config

    # #######################################
    # init constructor
    # #######################################

    def __init__(self) -> None:

        print('Init')
        
        # Try to set all intents

        intents = discord.Intents.all()
        super().__init__(command_prefix="!",intents=intents)
        self.prefix="!"
        self.configData=Config('config.json')
        #self.tree = app_commands.CommandTree(self)
        # The support command will ask for a thread title and description
        # and create a support thread for us

        @self.tree.command(name="support", description="Create a support thread")
        async def support(interaction: discord.Interaction):
            x : Support
            x= Support(gconfig=self.configData.readGuild(interaction.guild.id))
            await interaction.response.send_modal(x)

        @self.tree.command(name="setup", description="Define parameters for the bot")
        async def setup(interaction: discord.Interaction, 
                        support_channel:discord.TextChannel,
                        broadcast_channel:discord.TextChannel,
                        question_sleepcycles:int):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(f'only an Administrator can do that', ephemeral=True)
            else:
                try:
                    jData={
                            "IDLE_MESSAGE_CHANNEL_ID" : broadcast_channel.id,
                            "QUESTION_SLEEPING_TIME" : question_sleepcycles,
                            "SUPPORT_CHANNEL_ID" : support_channel.id
                          }
                    self.configData.writeGuild(interaction.guild.id,jData)
                    await interaction.response.send_message(f'All updated\nThank you for using my services!', ephemeral=True)
                except Exception as e:
                    print(f"ERROR in setup_hook: {e}")
                    await interaction.response.send_message(f'Ooops, there was a glitch!', ephemeral=True)


    # ################################
    # the bot run command just starts 
    # the bot with the token from
    # the json config file
    # ################################


    def  run(self,*args, **kwargs):
        super().run(token=self.configData.getToken())

    # #########################
    # setup_hook waits for the
    # command tree to sync
    # #########################

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        await self.tree.sync()
        try:
            for file in os.listdir("cogs"):
                if file.endswith(".py"):
                    name = file[:-3]
                    await self.load_extension(f"cogs.{name}")
        except Exception as e:
            print(f"ERROR in setup_hook: {e}")


    # ######################################################
    # on_ready is called once the client is initialized
    # ######################################################

    async def on_ready(self):
        print('Logged on as', self.user)
        self.task_scheduler.start()

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

        await self.process_commands(message)

        # reset the idle timer if a message has been sent or received
        self.channel_idle_timer = 0

        # question handling - we are monitoring if there have been questions

        qkey=message.guild.id
        
        # see if the guild is configured at all
        # if not, skip it

        guildData= self.configData.readGuild(qkey)

        if guildData is None:
            print (f"Guild {qkey} is not configured yet")
            return

        # see if the guild wants question handling at all
        # if not, skip it

        guildSleepTime=guildData['QUESTION_SLEEPING_TIME']
        if guildSleepTime > 0:
        
            # create a node for the last message in memory
            if self.last_question.get(qkey) is None:
                self.last_question[qkey] = {'asked':False,'messageID':0,'idleTime':0}

            # check if there is a question 
            if "?" in message.content:
                self.last_question[qkey]['asked']=True
                self.last_question[qkey]['messageID']=message.id
            else:
                self.last_question[qkey]['asked']=False
                self.last_question[qkey]['messageID']=0
        


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

    # ######################################################
    # find_message finds a message in a guild
    # there is no builtin way to o that from the Guilds class
    # so we need to loop through the text channels and see
    # if the message is there
    # ######################################################


    async def findMessage(theGuild : discord.Guild, ID):
        for theChannel in theGuild.text_channels:
            target=theChannel.fetch_message(ID)
            if (target):
                return target

   
    # ######################################################
    # task_scheduler is the main supervisor task
    # it runs every 10 minutes and checks the following:
    # - has a question been asked that has not been answered ?
    # - do reminders need to be sent out ?
    # - does a random message need to be sent out ?
    # ######################################################


    @tasks.loop(minutes=10)
    async def task_scheduler(self):

        # #####################################
        # See if there are unanswered questions
        # #####################################

        for theGuild in self.guilds:

            # see if the guild is configured at all
            # if not, skip it
            qkey= theGuild.id
            guildData= self.configData.readGuild(qkey)
            if guildData is None:
                print (f"Guild {qkey} is not configured yet")
                continue

            # if there is no last question then we skip as well 
            theNode=self.last_question.get(qkey)
            if theNode is None:
                continue
            if not theNode['asked']:
                continue

            question_ID=theNode['messageID']
            theNode['idleTime'] += 1

            # if the question is not expired then we skip again
            guildSleepTime=guildData['QUESTION_SLEEPING_TIME']
            if guildSleepTime == 0:
                continue
            if theNode['idleTime'] < guildSleepTime:
                continue

            # we have an expired question - let's find it

            try:
                theQuestion=self.findMessage(theGuild,question_ID)
                print(f"QUESTION from {theQuestion.author} WITHOUT REPLY {theQuestion.content}")
            except Exception as e:
                print(f"Scheduler question failed: {e}")
