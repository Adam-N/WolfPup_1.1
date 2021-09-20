import os
import json
import asyncio
import traceback
import traceback as tb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import discord
from discord.ext import commands
from master import Master
from lib.util import Util
from lib.mongo import Mongo
from cogs.level import Level
from cogs.triumphant import Triumphant
from cogs.mod import Mod
from cogs.wish import Buttons


def get_prefix(bot, message):
    if os.path.isfile(f'config/{str(message.guild.id)}/config.json'):
        with open(f'config/{str(message.guild.id)}/config.json', 'r') as f:
            config = json.load(f)
        prefixes = [config['prefix']]
    else:
        prefixes = ['*']
    return commands.when_mentioned_or(*prefixes)(bot, message)


initial_cogs = ['master', 'cogs.mod', 'cogs.welcome',
                'cogs.level', 'cogs.profile', 'cogs.thank', 'cogs.leaderboard', 'cogs.friend',
                'cogs.games', 'cogs.roles', 'cogs.starboard', 'cogs.timer', 'cogs.triumphant', 'cogs.wish',
                'cogs.lfg']

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix=get_prefix, description='A bot designed for GoldxGuns', intents=intents)
if __name__ == '__main__':
    for extension in initial_cogs:
        bot.load_extension(extension)
schedule = AsyncIOScheduler()


async def daily():
    """Daily Reset Timer"""
    for guild in bot.guilds:
        if os.path.isfile(f'config/{str(guild.id)}/config.json'):
            with open(f'config/{str(guild.id)}/config.json', 'r') as f:
                config = json.load(f)
        if config['channel_config']['config_channel']:
            config_channel = await bot.fetch_channel(config['channel_config']['config_channel'])

            # Daily Reset Functions Here
            await Util.reset_user_flags(Util(), config_channel)
            await Level.daily_bday_reset(Level(bot), guild)
            await config_channel.send(embed=discord.Embed(title=f'{config_channel.guild.name} Daily Reset!'))


async def weekly():
    """Weekly reset timer"""
    for guild in bot.guilds:
        if os.path.isfile(f'config/{str(guild.id)}/config.json'):
            with open(f'config/{str(guild.id)}/config.json', 'r') as f:
                config = json.load(f)
        if config['channel_config']['config_channel']:
            config_channel = bot.get_channel(config['channel_config']['config_channel'])
            # Weekly Reset Functions Here
            await triumphant_reset(guild)
            await config_channel.send(embed=discord.Embed(title=f'{config_channel.guild.name} Weekly Reset!'))


async def triumphant_reset(server):
    with open(f'config/{server.id}/config.json', 'r') as f:
        config = json.load(f)
    chan = bot.get_channel(int(config['triumphant_config']["triumph_channel"]))
    config_channel = bot.get_channel(config['channel_config']['config_channel'])

    await config_channel.send('Starting Weekly Reset')

    if os.path.isfile(f'config/{server.id}/triumphant_copy.json'):
        os.remove(f'config/{server.id}/triumphant_copy.json')
    with open(f'config/{server.id}/triumphant.json', 'r') as f:
        users = json.load(f)

    with open(f'config/{server.id}/triumphant_copy.json', 'w') as f:
        json.dump(users, f)

    os.remove(f'config/{server.id}/triumphant.json')

    triumphant = {}

    with open(f'config/{str(server.id)}/triumphant.json', 'w') as f:
        json.dump(triumphant, f)

    reset_embed = discord.Embed(title="\U0001f5d3| New Week Starts Here. Get that bread!")

    await chan.send(embed=reset_embed)


async def cactpot():
    """Cactpot Reminder"""
    for server in bot.guilds:
        with open(f'config/{str(server.id)}/config.json', 'r') as f:
            config = json.load(f)
        role = server.get_role(int(config['role_config']['cactpot']))
        channel = bot.get_channel(int(config['channel_config']['cactpot']))
        if channel:
            return
        embed = discord.Embed(title='**The JumboCactPot has been drawn!**', description="Don't forget to check your "
                                                                                        "tickets within the hour for the "
                                                                                        "Early Bird bonus (+7%). If the "
                                                                                        "Jackpot II action isn't activated"
                                                                                        " on the Free Company, then please "
                                                                                        "activate it now.")
        embed.set_image(url="https://img.finalfantasyxiv.com/lds/blog_image/jp_blog/jp20170607_iw_04.png")

        await channel.send(f'{role.ment}')
        await channel.send(embed=embed)


async def monthly():
    """Monthly reset timer"""
    for guild in bot.guilds:
        if os.path.isfile(f'config/{str(guild.id)}/config.json'):
            with open(f'config/{str(guild.id)}/config.json', 'r') as f:
                config = json.load(f)
        if config['channel_config']['config_channel']:
            try:
                config_channel = await bot.fetch_channel(config['channel_config']['config_channel'])
            except discord.errors.NotFound:
                continue
            # Monthly Reset Functions Here
            await Mod.award_monthly_roles(Mod(bot), guild)
            await Level.build_level(Level(bot), config_channel)
            await Level.remove_levels_monthly(Level(bot), config_channel.guild)
            await config_channel.send(embed=discord.Embed(title=f'{config_channel.guild.name} Monthly Reset!'))

@bot.event
async def on_error(event, *args, **kwargs):
    config_channel = None
    if os.path.isfile('config/334925467431862272/config.json'):
        with open('config/334925467431862272/config.json', 'r') as f:
            config = json.load(f)
        config_channel = await bot.fetch_channel(config['channel_config']['config_channel'])
    else:
        return
    new_embed = discord.Embed(title=f'**[Error]** {type(event).__name__} **[Error]**')
    new_embed.add_field(name='Event', value=event)
    traceback_text = '```py\n%s\n```' % traceback.format_exc()
    if len(traceback_text) > 600:
        traceback_text = traceback_text[0:600]
    new_embed.description = traceback_text
    new_embed.add_field(name="Args", value=f"{args}")

    await config_channel.send(embed=new_embed)


@bot.event
async def on_command_error(event, *args, **kwargs):
    config_channel = None
    message = event.message
    if os.path.isfile(f'config/{str(message.guild.id)}/config.json'):
        with open(f'config/{str(message.guild.id)}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = await bot.fetch_channel(config['channel_config']['config_channel'])
    else:
        return
    new_embed = discord.Embed(title=f'**[Command Error]** {type(event).__name__} **[Command Error]**')
    await message.channel.send('There was an error. If this continues please send a message in '
                               '#help_and_feedback or message Adam or Wolf', delete_after=6)
    await message.delete()
    new_embed.add_field(name="Event", value=f"{args}")
    new_embed.add_field(name='User', value=f"{message.author.display_name}")
    new_embed.add_field(name='Channel', value=f"{message.channel.name}")
    new_embed.add_field(name='Content', value=f"{message.content}")
    new_embed.description = f'```py\n{traceback.format_exc()}\n```'

    if kwargs:
        new_embed.add_field(name="Arguments", value=f"{kwargs}")
    await config_channel.send(embed=new_embed)


async def change_presence():
    game = discord.Game(";help for more information")
    await bot.change_presence(status=discord.Status.idle, activity=game)


@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}')
    print(f'Successfully logged in and booted...!')
    for guild in bot.guilds:
        if not os.path.isdir(f'config/{guild.id}/'):
            os.makedirs(f'config/{guild.id}/')
    bot.add_view(Buttons(bot))
    asyncio.create_task(change_presence())


@bot.command()
async def get_jobs(ctx):
    schedule.print_jobs()
    await ctx.send(schedule.print_jobs())


async def on_disconnect():
    schedule.shutdown(wait=False)
    return


print('\nLoading token and connecting to client...')
token = open('token.txt', 'r').readline()
schedule.add_job(daily, 'cron', day='*', hour=18)
schedule.add_job(weekly, 'cron', week='*', day_of_week='sat', hour=22)
schedule.add_job(monthly, 'cron', month='*', day='1')
schedule.start()
bot.run(token, reconnect=True)
