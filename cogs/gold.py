import json
import datetime as dt
import discord
import pytz
from discord import Forbidden
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo


class Gold(commands.Cog, name='Gold'):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None

    @commands.command(name='build_gold', hidden=True, aliases=['rebuild_gold'])
    @commands.is_owner()
    async def build_gold(self, ctx, member: discord.Member = None, pending=None):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding Gold stats...'))
        else:
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding Gold stats...'))
        if await Util.check_channel(ctx, True):
            new_level = {'gold': {'amount': 0, 'timestamp': discord.utils.utcnow(), 'daily_count': 0, 'streak': 0},
                         'flags': {'daily': True, 'daily_stamp': discord.utils.utcnow(), 'thank': True}}
            if member:
                self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': new_level}, upsert=True)
                await pending.edit(embed=discord.Embed(title='Done'))
                return
            else:
                for member in ctx.guild.members:
                    if not member.bot:
                        self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': new_level}, upsert=True)
            await pending.edit(embed=discord.Embed(title='Gold Stats Reset'))
            return pending

    @commands.is_owner()
    async def build_bday(self, ctx, member: discord.Member = None, pending=None):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding Bday stats...'))
        else:
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding Bday stats...'))
        if await Util.check_channel(ctx, True):
            new_bday = {'bday': {'timestamp': discord.utils.utcnow() - dt.timedelta(days=366)}}
            if member and not member.bot:
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_bday}, upsert=True)
                await pending.edit(embed=discord.Embed(title='Done'))
                return
            else:
                for member in ctx.guild.members:
                    if not member.bot:
                        self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_bday}, upsert=True)
            await ctx.send(embed=discord.Embed(title='Bday Stats Reset'))
            return pending

    @commands.command(name='daily')
    async def daily(self, ctx, member: discord.Member = None):
        """Use to claim your daily exp bonus or give to a friend!"""
        async with ctx.channel.typing():
            try:
                # Initiates server and other variables.
                self.server_db = self.db[str(ctx.guild.id)]['users']
                broken_streak = False
                if member is None:
                    member = ctx.author

                # Checks if it is in a bot channel.
                if await Util.check_channel(ctx, True):
                    # Increases the daily streak
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$inc': {'gold.exp_streak': 1}})

                    # Gets the user database.
                    user = self.server_db.find_one({'_id': str(ctx.author.id)})

                    # Flags are for checking if daily has been used yet.
                    if user['flags']['daily']:

                        # Gets the streak for the user.
                        streak = user['gold']['exp_streak']

                        # Starts building the embed
                        new_embed = discord.Embed(title='You\'ve claimed your daily bonus!',
                                                  color=discord.Colour.gold())
                        new_embed.set_thumbnail(
                            url='https://cdn.discordapp.com/attachments/532380077896237061/800924153053970476'
                                '/terry_coin.png')

                        # If the person getting the daily is a different persom they get a bonus.
                        if member != ctx.author:
                            new_embed.title = 'You\'ve given your bonus to your friend!'
                            friend_value = 2
                        else:
                            friend_value = 1

                        # Checks to see if the last time they used daily was more than 36 hours ago
                        if (user['flags']['daily_stamp'].replace(tzinfo=pytz.timezone("UTC")) + dt.timedelta(
                                hours=36)) < discord.utils.utcnow():
                            # Changes information based on the missed streak.
                            new_embed.description = f'This is day {streak}. You missed your streak window...'
                            self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                               {'$set': {'gold.exp_streak': 0}})
                            streak = 0
                            broken_streak = True

                        if not broken_streak:

                            # Checks and changes information if the streak 5 days in a row.
                            if streak >= 5:
                                new_embed.description = '__BONUS__ This is your 5-day streak! __BONUS__'
                                self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                                   {'$set': {'gold.exp_streak': 0}})
                            else:
                                new_embed.description = f'This is day {streak}. Keep it up to day 5!'

                        # Gets the level from the users roles.
                        level = await self.get_level(ctx.author)

                        # How much the gold value is going to increase by.
                        change_value = ((2 * friend_value) + (1 * streak) * level)

                        # Changes the information in the database.
                        self.server_db.find_one_and_update({'_id': str(member.id)},
                                                           {'$inc': {'gold.amount': change_value}})
                        self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                           {'$set': {'flags.daily': False}})
                        self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                           {'$set': {'flags.daily_stamp': discord.utils.utcnow()}})
                        await ctx.send(embed=new_embed)

                        # Logs the information to the log channel
                        await self.gold_log(member.guild, member, change_value, ctx.channel, True, "Daily")
                    else:
                        # Deals with if someone already claimed their daily bonus.
                        await ctx.message.delete()
                        await ctx.send(
                            embed=discord.Embed(title='You\'ve already claimed your daily bonus today!'),
                            delete_after=5)

            except Exception as e:
                raise KeyError(f"{e}, something went wrong with Daily")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Deletes the user when they leave the server.
        self.server_db = self.db[str(member.guild.id)]['users']
        self.server_db.find_one_and_delete({'_id': str(member.id)})

    @commands.command(hidden=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def gold(self, ctx, give: str = None, user: discord.Member = None, change: int = None):
        give = give.lower()
        # Checks if the value of give is one of two options.
        if give != "give" and give != 'take':
            return
        # Preparing for negative numbers.
        if change < 0:
            change = abs(change)
        # Can't use a 0 to change values and makes sure change isn't empty.
        if change == 0 or change is None:
            ctx.send(f"You need to {'have a number other than 0.' if change == 0 else 'add an amount of gold to give'}"
                     , delete_after=5)
        # If no user, no one to give gold to.
        if user is None:
            return
        # Makes change negative in gold is being taken
        if give == 'take':
            change = -change

        # Gets db information
        self.server_db = self.db[str(ctx.guild.id)]['users']
        user = self.server_db.find_one({'_id': str(ctx.author.id)})

        # Checks for negative gold
        if user['gold']['amount'] - change < 0:
            await ctx.sent('User cannot have a negative amount of Gold', delete_after=5)
            return

        # Changes the gold
        self.server_db.find_one_and_update({'_id': str(user.id)},
                                           {'$inc': {'gold.amount': change}})
        # Sends message confirming gold has changed.
        await ctx.send(embed=discord.Embed(title=f"You {'took' if change < 0 else 'gave'} {abs(change)} gold "
                                                 f"{'from' if change < 0 else 'to'} {user.display_name}."))
        # Logs gold change
        await self.gold_log(ctx.guild, user, change, ctx.channel, True, f"{'Take' if change < 0 else 'Give'} Gold")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def prune_members(self, ctx):
        """For Removing Members from the DB who are no longer in the server"""
        # Opens Config file and loads the config channel
        with open(f'config/{str(ctx.guild.id)}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = self.bot.get_channel(int(config['channel_config']['config_channel']))

        # Gets server information
        self.server_db = self.db[str(ctx.guild.id)]['users']

        # Iterates through each user in the data base, and checks to see if they are an actual user on the server.
        for user in self.server_db:
            try:
                # This will return as none if the user is not on the server.
                test_user = self.bot.get_user(int(user["_id"]))
                if test_user:
                    continue
                # Deletes the information from the DB if they aren't on the server.
                elif not test_user:
                    self.server_db.find_one_and_delete({'_id': int(user["_id"])})
            except:
                # For catching big screw ups.
                await config_channel.send('Adam, you really fucked it up this time... ')
                continue
        # Confirmation message
        await config_channel.send("Complete")

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def birthday(self, ctx, member: discord.Member):
        """Wish a user a happy birthday!"""
        # Gets DB information
        self.server_db = self.db[str(ctx.guild.id)]['users']
        # Opens config file
        with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        # Gets user information from the DB
        user = self.server_db.find_one({'_id': str(ctx.author.id)})
        # Checks to see if the user has already been wished a birthday. 363 days just to have a buffer.
        if discord.utils.utcnow() <= user['bday']['timestamp'].replace(tzinfo=pytz.timezone("UTC")) + dt.timedelta(
                days=363):
            day_delay_embed = discord.Embed(title="\U0001f550 You have to wait until next year! \U0001f550 ")
            await ctx.send(embed=day_delay_embed)
            return

        # Gets appropriate roles to use.
        he_role = discord.utils.get(ctx.message.guild.roles, name='He/Him')
        she_role = discord.utils.get(ctx.message.guild.roles, name='She/Her')
        birthday_role = ctx.message.guild.get_role(int(config['role_config']['birthday']))

        # Gets pronouns for the message. Defaults to them if they don't have a role.
        if he_role in member.roles:
            pronoun = 'him'
        elif she_role in member.roles:
            pronoun = 'her'
        else:
            pronoun = 'them'

        # Starts building the birthday embed.
        birthday_embed = discord.Embed(title='\U0001f389 Happy Birthday! \U0001f389',
                                       description=f"Wish {member.display_name} a happy birthday! Let's celebrate "
                                                   f"with {pronoun}!")
        birthday_embed.add_field(name="\U0001f382",
                                 value="Good work on makin' it round the sun again without biting the dust!"
                                       "Hopefully it wasn't too boring! \n"
                                       "Really though, thanks for being a part of our little posse. May your RNG"
                                       "be extra nice today and the year full of happiness and prosperity. "
                                       "Sending love from all of us here at GxG")
        # Sends the embed and a message that mentions the user.
        channel = self.bot.get_channel(int(config['channel_config']['lounge']))
        await channel.send(f'Happy Birthday {member.mention}')
        await channel.send(embed=birthday_embed)

        # Gives the user the birthday role.
        await member.add_roles(birthday_role)
        self.server_db.find_one_and_update({'_id': str(member.id)},
                                           {'$set': {'bday.timestamp': discord.utils.utcnow()}})
        # Adds gold for the user.
        self.server_db.find_one_and_update({'_id': str(member.id)},
                                           {'$inc': {'gold.amount': 3000}})
        # Logs gold change.
        await self.gold_log(ctx.guild, member, 3000, channel=None, command=True, name="Birthday")

    async def daily_bday_reset(self, guild):
        # Gets DB information
        self.server_db = self.db[str(guild.id)]['users']
        # Loads config
        with open(f'config/{guild.id}/config.json', 'r') as f:
            config = json.load(f)
        # Gets bday role.
        birthday_role = guild.get_role(int(config['role_config']['birthday']))

        # Checks users who have the birthday role and removes it if they've had it for more than 16 hours.
        for member in birthday_role.members:
            user = self.server_db.find_one({'_id': str(member.id)})
            if discord.utils.utcnow() >= user['bday']['timestamp'].replace(
                    tzinfo=pytz.timezone("UTC")) + dt.timedelta(hours=16):
                try:
                    await member.remove_roles(birthday_role)
                except Forbidden:
                    raise Forbidden("I don't have the permissions to remove birthday role.")

    async def get_level(self, user):
        # Gets the user's level role.
        for x in range(1, 5):
            if f"Level {x}" in user.roles:
                return x
        return 1

    @commands.Cog.listener()
    async def on_message(self, message):
        # Checks if the message was in a DM.
        if isinstance(message.channel, discord.DMChannel):
            return
        # If the user isn't a bot, and it isn't in a channel that gaining gold has been blacklisted from.
        if not message.author.bot and await Util.check_exp_blacklist(message):
            # Gets DB information.
            self.server_db = self.db[str(message.guild.id)]['users']
            user = self.server_db.find_one({'_id': str(message.author.id)})
            # Checks if the user has earned gold in the specified timeframe.
            # Daily Count makes sure they don't get it more than 3 times in a day.
            if (user['gold']['timestamp'].replace(tzinfo=pytz.timezone("UTC")) + dt.timedelta(
                    seconds=3)) <= discord.utils.utcnow() and user['gold']['daily_count'] < 3:
                # Sets the gold timestamp.
                self.server_db.update_one({'_id': str(message.author.id)}, {'$set':
                    {'gold.timestamp': discord.utils.utcnow()}})
                # Calculates the amount of gold that will be earned then adds it to their information.
                gold_change = 2 * (await self.get_level(message.author))
                self.server_db.find_one_and_update({'_id': str(message.author.id)},
                                                   {'$inc': {'gold.amount': gold_change}})
                # Increases the daily count.
                # self.server_db.find_one_and_update({'_id': str(message.author.id)},
                #                                   {'$inc': {'gold.daily_count': 1}})
                # Logs gold change.
                await self.gold_log(message.guild, message.author, gold_change, message.channel)
            """except KeyError:
                self.server_db.update_one({'_id': str(message.author.id)}, {'$set':
                    {
                        'gold.timestamp': discord.utils.utcnow()}})
            except TypeError:
                with open(f'config/{str(message.guild.id)}/config.json', 'r') as f:
                    config = json.load(f)
                config_channel = self.bot.get_channel(int(config['channel_config']['config_channel']))
                await config_channel.send('Error in On Message')"""

    @commands.command(hidden=True)
    @commands.is_owner()
    async def manual_daily_reset(self, ctx):
        # Get's DB information
        self.server_db = self.db[str(ctx.guild.id)]['users']
        # Base values for the reset.
        reset_flags = {'flags': {'daily': True, 'daily_stamp': None, 'thank': True}}
        # Resets all the values for all members.
        for member in ctx.guild.members:
            if not member.bot:
                self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': reset_flags})
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set':
                                                                                 {'gold.daily_count': 0}})

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Gets the booster role.
        booster_role = discord.utils.get(before.guild.roles, name='Confidants / Boost')
        # Checks if the user was boosting already.
        if booster_role in before.roles:
            return
        # Checks if they are now boosting.
        if booster_role in after.roles:
            # Gets the user information.
            self.server_db = self.db[str(after.guild.id)]['users']
            # Adds the gold to the users profile.
            self.server_db.find_one_and_update({'_id': str(after.id)}, {'$inc': {'gold.amount': 3000}})
            # Logs the information.
            await self.gold_log(after.guild, after, 3000, command=True, name="Booster Role")

    async def gold_log(self, guild, member, change, channel=None, command: bool = False, name=None):
        # Opens config gets the channel, and gets DB information
        with open(f'config/{guild.id}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = self.bot.get_channel(config['channel_config']['gold_channel'])
        self.server_db = self.db[str(guild.id)]['users']
        user = self.server_db.find_one({'_id': str(member.id)})
        # Builds the embed
        embed = discord.Embed(
            title=f"{member.display_name} has had a change to their gold{f' in {channel.name}' if channel is not None else '.'}")
        embed.add_field(name="User ID:", value=f"{member.id}")
        embed.add_field(name="Gold Change:", value=f"{change}")
        if command:
            embed.add_field(name="Given by Command", value=f"{name}")
        embed.set_footer(text=f"Gold Total: {user['gold']['amount']}")
        # Sends the embed
        await config_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Gold(bot))
