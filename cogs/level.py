import os
import json
import random
import asyncio
import traceback
from math import sqrt, floor
import datetime as dt
import discord
import pytz
from discord import Forbidden
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo
from pymongo import ReturnDocument


class Level(commands.Cog, name='Level'):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None

    @commands.command(name='build_level', hidden=True, aliases=['rebuild_level'])
    @commands.is_owner()
    async def build_level(self, ctx, member: discord.Member = None, pending=None):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding Level stats...'))
        else:
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding Level stats...'))
        if await Util.check_channel(ctx, True):
            new_level = {'level': 1, 'exp': 0, 'exp_streak': 0, 'timestamp': discord.utils.utcnow(),
                         'flags': {'daily': True, 'daily_stamp': discord.utils.utcnow(), 'thank': True}}
            if member:
                self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': new_level}, upsert=True)
                return
            for member in ctx.guild.members:
                if not member.bot:
                    self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': new_level}, upsert=True)
            await pending.edit(embed=discord.Embed(title='Done'))
            return pending

    @staticmethod
    async def remove_levels_monthly(self, guild: discord.guild):
        with open(f'config/{guild.id}/config.json', 'r') as f:
            config = json.load(f)
        roles_check = [guild.get_role(config['role_config']['level_2']),
                       guild.get_role(config['role_config']['level_3']),
                       guild.get_role(config['role_config']['level_4']),
                       guild.get_role(config['role_config']['level_5'])]

        for user in guild.users:
            for role in user.roles:
                if role in roles_check:
                    await user.remove_roles(role)

    @commands.command(name='stats', pass_context=True)
    async def stats(self, ctx, member: discord.Member = None):
        """Returns a user's current profile level and experience"""
        await ctx.message.delete()
        member = member or ctx.author
        if await Util.check_channel(ctx, True):
            await self.add_experience(ctx, member, 0)

    @commands.command(name='daily')
    async def daily(self, ctx, member: discord.Member = None):
        """Use to claim your daily exp bonus or give to a friend!"""
        async with ctx.channel.typing():
            try:
                self.server_db = self.db[str(ctx.guild.id)]['users']
                broken_streak = False
                if member is None:
                    member = ctx.author
                if await Util.check_channel(ctx, True):
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$inc': {'exp_streak': 1}})
                    user = self.server_db.find_one({'_id': str(ctx.author.id)})
                    if user['flags']['daily']:
                        streak = user['exp_streak']
                        new_embed = discord.Embed(title='You\'ve claimed your daily bonus!',
                                                  color=discord.Colour.gold())
                        new_embed.set_thumbnail(
                            url='https://cdn.discordapp.com/attachments/532380077896237061/800924153053970476'
                                '/terry_coin.png')
                        if member != ctx.author:
                            new_embed.title = 'You\'ve given your bonus to your friend!'
                        try:
                            if (user['flags']['daily_stamp'].astimezone(tz=pytz.timezone("UTC")) + dt.timedelta(hours=36)) < discord.utils.utcnow():
                                new_embed.description = f'This is day {streak}. You missed your streak window...'
                                self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                                   {'$set': {'exp_streak': 0}})
                                streak -= 1
                                broken_streak = True
                        except:
                            pass
                        if not broken_streak:
                            if streak >= 5:
                                new_embed.description = '__BONUS__ This is your 5-day streak! __BONUS__'
                                self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                                   {'$set': {'exp_streak': 0}})
                                streak = 10
                            else:
                                new_embed.description = f'This is day {streak}. Keep it up to day 5!'
                        self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                           {'$set': {'flags.daily': False}})
                        self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                           {'$set': {'flags.daily_stamp': discord.utils.utcnow()}})
                        daily_exp = int(random.randint(150, 250) * (1 + (0.15 * streak)))
                        await self.update_experience(ctx.guild.id, member.id, daily_exp)
                        await ctx.send(embed=new_embed)
                    else:
                        await ctx.message.delete()
                        pending = await ctx.send(
                            embed=discord.Embed(title='You\'ve already claimed your daily bonus today!'))
                        await asyncio.sleep(5)
                        await pending.delete()
            except Exception as e:
                raise KeyError(f"{e}, something went wrong with Daily")

    @commands.command(name='add_experience', hidden=True, pass_context=True, aliases=['xp'])
    @commands.has_guild_permissions(administrator=True)
    async def add_experience(self, ctx, member: discord.Member, amount: int):
        """Used to award exp to a specified user"""
        if await Util.check_channel(ctx):
            if isinstance(member, discord.Member):
                user_level, user_exp = await self.update_experience(ctx.guild.id, member.id, amount)

                new_embed = discord.Embed(title=f'{member.display_name}\'s Stats',
                                          color=discord.Colour.gold())
                new_embed.add_field(name=f'**Level :**',
                                    value=user_level)
                new_embed.add_field(name=f'**Experience :**',
                                    value=user_exp)
                await ctx.send(embed=new_embed)

    @staticmethod
    def update_level(xp):
        level = floor(((sqrt(40 + xp)) / 110) + 1)
        if level > 5:
            level = 5
        return level

    async def update_experience(self, guild_id, user_id, amount: int = None):
        if os.path.isfile(f'config/{guild_id}/config.json'):
            with open(f'config/{guild_id}/config.json', 'r') as f:
                config = json.load(f)
        self.server_db = self.db[str(guild_id)]['users']
        if amount is None:
            amount = random.randint(100, 150)
        guild = await self.bot.fetch_guild(int(guild_id))
        member = await guild.fetch_member(int(user_id))
        user = self.server_db.find_one_and_update({'_id': str(user_id)}, {'$inc': {'exp': amount}},
                                                  return_document=ReturnDocument.AFTER)
        user = self.server_db.find_one_and_update({'_id': str(user_id)},
                                                  {'$set': {'level': self.update_level(user['exp'])}},
                                                  return_document=ReturnDocument.AFTER)
        try:
            if guild.get_role(config['role_config'][f'level_{user["level"]}']) not in member.roles:
                await member.add_roles(guild.get_role(config['role_config'][f'level_{user["level"]}']))

                for x in range(1, 4):
                    if guild.get_role(config['role_config'][f'level_{x + 1}']) in member.roles:
                        await member.remove_roles(guild.get_role(config['role_config'][f'level_{x + 1}']))
        except KeyError:
            pass
            if 1 < user["level"] <= 5:
                await member.add_roles(guild.get_role(config['role_config'][f'level_{user["level"]}']))
        await self.generate_top_5(guild.id)
        return user['level'], user['exp']

    async def generate_top_5(self, guild_id):
        if os.path.isfile(f'config/{guild_id}/config.json'):
            with open(f'config/{guild_id}/config.json', 'r') as f:
                config = json.load(f)
        self.server_db = self.db[str(guild_id)]['users']
        guild = self.bot.get_guild(guild_id)
        users = self.server_db.find().sort('exp', -1)[0:20]
        blacklist = False
        top_5 = []
        top_5_role = guild.get_role(config['role_config']['top_5'])

        for user in users:
            try:
                member = await guild.fetch_member(int(user['_id']))
            except discord.errors.NotFound:
                continue
            blacklist = False
            for role in member.roles:
                if role.id in config['role_config']['top_5_blacklist']:
                    blacklist = True
                    break
            if not blacklist:
                top_5.append(int(user['_id']))
            if len(top_5) == 5:
                break
        for user_id in top_5:
            member = await guild.fetch_member(user_id)
            if member.id in top_5 and top_5_role not in member.roles:
                await member.add_roles(top_5_role)
        for member in top_5_role.members:
            if member.id not in top_5:
                await member.remove_roles(top_5_role)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.server_db = self.db[str(member.guild.id)]['users']
        self.server_db.find_one_and_delete({'_id': str(member.id)})

    @commands.command(hidden=True)
    @commands.is_owner()
    async def prune_members(self, ctx):
        with open(f'config/{str(ctx.guild.id)}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = self.bot.get_channel(int(config['channel_config']['config_channel']))
        self.server_db = self.db[str(ctx.guild.id)]['users']
        for user in self.server_db:
            try:
                test_user = self.bot.get_user(int(user["_id"]))
                if test_user:
                    continue
                elif not test_user:
                    self.server_db.find_one_and_delete({'_id': int(user["_id"])})
            except:
                await config_channel.send('Adam, you really fucked it up this time... ')
                continue
        await config_channel.send("Complete")

    @commands.command(name='build_bday', hidden=True, aliases=['rebuild_bday'])
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
                return
            for member in ctx.guild.members:
                if not member.bot:
                    self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_bday}, upsert=True)
            await pending.edit(embed=discord.Embed(title='Done'))
            return pending

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def birthday(self, ctx, member: discord.Member):
        """Wish a user a happy birthday!"""
        self.server_db = self.db[str(ctx.guild.id)]['users']
        with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        user = self.server_db.find_one({'_id': str(ctx.author.id)})
        try:
            if discord.utils.utcnow() <= user['bday']['timestamp'] + dt.timedelta(days=364):
                day_delay_embed = discord.Embed(title="\U0001f550 You have to wait until next year! \U0001f550 ")
                await ctx.send(embed=day_delay_embed)
                return
        except KeyError:
            pass
        except UnboundLocalError:
            pass
        he_role = discord.utils.get(ctx.message.guild.roles, name='He/Him')
        she_role = discord.utils.get(ctx.message.guild.roles, name='She/Her')
        they_role = discord.utils.get(ctx.message.guild.roles, name='They/Them')
        birthday_role = ctx.message.guild.get_role(int(config['role_config']['birthday']))

        if he_role in member.roles:
            birthday_embed = discord.Embed(title='\U0001f389 Happy Birthday! \U0001f389',
                                           description=f"Wish {member.display_name} a happy birthday! Let's celebrate "
                                                       f"with him!")
        elif she_role in member.roles:
            birthday_embed = discord.Embed(title='\U0001f389 Happy Birthday! \U0001f389',
                                           description=f"Wish {member.display_name} a happy birthday! Let's celebrate "
                                                       f"with her!")
        elif member in they_role.members:
            birthday_embed = discord.Embed(title='\U0001f389 Happy Birthday! \U0001f389',
                                           description=f"Wish {member.display_name} a happy birthday! Let's celebrate "
                                                       f"with them!' ")
        else:
            birthday_embed = discord.Embed(title='\U0001f389 Happy Birthday! \U0001f389',
                                           description=f"Wish {member.display_name} a happy birthday! Let's celebrate "
                                                       f"with them!")
        birthday_embed.add_field(name="\U0001f382",
                                 value="Good work on makin' it round the sun again without biting the dust, haha!"
                                       "Hopefully it wasn't too boring! \n"
                                       "Really though, thanks for being a part of our little posse. May your RNG"
                                       "be extra nice today and the year full of happiness and prosperity. "
                                       "Sending love from all of us here at GxG")
        channel = self.bot.get_channel(int(config['channel_config']['lounge']))
        await channel.send(f'Happy Birthday {member.mention}')
        await channel.send(embed=birthday_embed)

        await member.add_roles(birthday_role)
        self.server_db.find_one_and_update({'_id': str(member.id)},
                                           {'$set': {'bday.timestamp': discord.utils.utcnow()}})

    @staticmethod
    async def daily_bday_reset(self, guild):
        try:
            self.server_db = self.db[str(guild.id)]['users']
            with open(f'config/{guild.id}/config.json', 'r') as f:
                config = json.load(f)
            birthday_role = guild.get_role(int(config['role_config']['birthday']))
            for member in birthday_role.members:
                user = self.server_db.find_one({'_id': str(member.id)})
                try:
                    if discord.utils.utcnow() >= user['bday']['timestamp'] + dt.timedelta(hours=16):
                        try:
                            await member.remove_roles(birthday_role)
                        except Forbidden:
                            raise Forbidden("I don't have the permissions to remove birthday role.")
                except KeyError:
                    continue
        except TypeError:
            return

    @commands.Cog.listener()
    async def on_message(self, message):

        if isinstance(message.channel, discord.DMChannel):
            return
        if not message.author.bot and await Util.check_exp_blacklist(message):
            self.server_db = self.db[str(message.guild.id)]['users']
            user = self.server_db.find_one({'_id': str(message.author.id)})

            # try:
            if (user['timestamp'].astimezone(tz=pytz.timezone("UTC")) + dt.timedelta(
                    seconds=45)) <= discord.utils.utcnow():
                self.server_db.update_one({'_id': str(message.author.id)}, {'$set':
                                                                                {'timestamp': discord.utils.utcnow()}})
                await self.update_experience(message.guild.id, message.author.id)
            '''except KeyError:
                self.server_db.update_one({'_id': str(message.author.id)}, {'$set':
                                                                                {'timestamp': discord.utils.utcnow()}})
            except TypeError:
                raise TypeError('Problem with the timezones in level.py')'''

    @commands.command(hidden=True)
    @commands.is_owner()
    async def manual_daily_reset(self, ctx):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        reset_flags = {'flags': {'daily': True, 'daily_stamp': None, 'thank': True}}
        for member in ctx.guild.members:
            if not member.bot:
                self.server_db.find_one_and_update({"_id": str(member.id)}, {'$set': reset_flags})


def setup(bot):
    bot.add_cog(Level(bot))
