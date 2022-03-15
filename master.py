import os
import json
import asyncio
import discord
from discord.ext import commands
from time import time
import datetime as dt

from cogs.gold import Gold
from cogs.starboard import Starboard
from lib.mongo import Mongo
from cogs.level import Level
from cogs.profile import Profile
from cogs.thank import Thank
from lib.util import Util


class Master(commands.Cog, name='Master'):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None
        self.start_time = time()
        self.sys_aliases = {'ps': {'ps', 'psn', 'ps4', 'ps5', 'playstation'},
                            'steam': {'steam', 'steam64', 'valve'},
                            'dtg': {'destiny', 'bungie', 'Bungie', 'destiny2'},
                            'xiv': {'ffxiv', 'xiv', 'ff'}}

    @commands.command(name='ping')
    @commands.is_owner()
    async def ping(self, ctx):
        """Shows the bot ping in milliseconds."""
        if await Util.check_channel(ctx, True):
            await ctx.send(f':ping_pong: **Pong!**⠀{round(self.bot.latency, 3)}ms')

    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Shows the uptime for the bot."""
        if await Util.check_channel(ctx, True):
            current_time = time()
            difference = int(round(current_time - self.start_time))
            time_converted = dt.timedelta(seconds=difference)
            Util.deltaconv(int(time_converted.total_seconds()))
            new_embed = discord.Embed()
            new_embed.add_field(name="Uptime", value=f'{Util.deltaconv(int(time_converted.total_seconds()))}',
                                inline=True)
            new_embed.set_thumbnail(url='https://media.discordapp.net/attachments/742389103890268281/746419792000319580'
                                        '/shiinabat_by_erickiwi_de3oa60-pre.png?width=653&height=672')
            await ctx.send(embed=new_embed)

    @commands.command(name='change_prefix', hidden=True, aliases=['prefix'])
    @commands.is_owner()
    async def change_prefix(self, ctx, prefix: str):
        """Administrator command"""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            if ctx.channel.id == config['channel_config']['config_channel']:
                if len(prefix) > 3:
                    await ctx.send(embed=discord.Embed(title='Bot prefix must be 3 or less characters'))
                    return
                config['prefix'] = prefix
                with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                await ctx.send(embed=discord.Embed(title=f'Prefix changed to \"{prefix}\"'))

    @commands.command(name='reset_config', hidden=True, aliases=['init_config'])
    @commands.is_owner()
    async def reset_config(self, ctx):
        await Util.reset_config(ctx)

    @commands.command(name='config', hidden=True, aliases=['cfg'])
    @commands.is_owner()
    async def config(self, ctx, cfg: str, setting: str, value, delete: str = None):
        """Administrator command"""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            try:
                value = await commands.TextChannelConverter().convert(ctx, value)
                value = value.id
            except (TypeError, commands.errors.ChannelNotFound):
                pass
            try:
                value = await commands.RoleConverter().convert(ctx, value)
                value = value.id
            except (TypeError, commands.errors.RoleNotFound):
                pass
            try:
                value = await commands.EmojiConverter().convert(ctx, value)
            except (TypeError, commands.errors.EmojiNotFound):
                pass
            try:
                if value.isdigit():
                    value = int(value)
            except AttributeError:
                pass
            try:
                if isinstance(config[cfg][setting], list):
                    if delete == '-r':
                        config[cfg][setting].remove(value)
                    else:
                        config[cfg][setting].append(value)
                else:
                    config[cfg][setting] = value
            except KeyError:
                await ctx.send(embed=discord.Embed(title=f'**[Error]** : \"{setting}\" is not defined'))
                return
            with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=2)
            await ctx.send(embed=discord.Embed(title='Updated configuration',
                                               description=f'**Config** : {cfg}\n**Setting** : {setting}'))

    @commands.command(aliases=['setstatus', 'botstatus'], hidden=True)
    @commands.is_owner()
    async def status(self, ctx, arg: str, *status: str):
        """Administrator command"""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            if ctx.channel.id == config['channel_config']['config_channel']:
                arg = arg.lower()
                joined_status = " ".join(status)
                if arg not in ['playing', 'listening', 'watching']:
                    await ctx.send('Only playing, streaming, listening or watching allowed as activities.',
                                   delete_after=5)
                    return
                if arg == 'playing':
                    await self.bot.change_presence(activity=discord.Game(name=joined_status))
                if arg == 'listening':
                    await self.bot.change_presence(
                        activity=discord.Activity(type=discord.ActivityType.listening, name=joined_status))
                if arg == 'watching':
                    await self.bot.change_presence(
                        activity=discord.Activity(type=discord.ActivityType.watching, name=joined_status))
                await ctx.send(f'status changed to {arg} {joined_status}')

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        """Administrator command."""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            if ctx.channel.id == config['channel_config']['config_channel']:
                try:
                    self.bot.load_extension(cog)
                except Exception as e:
                    await discord.Message.add_reaction(ctx.message, '\U0000274E')
                    error = await ctx.send(f'Failed to load module: {type(e).__name__} - {e}')
                    await asyncio.sleep(10)
                    await error.delete()
                else:
                    await discord.Message.add_reaction(ctx.message, '\U00002705')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        """Administrator command."""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            if ctx.channel.id == config['channel_config']['config_channel']:
                try:
                    self.bot.unload_extension(cog)
                except Exception as e:
                    await discord.Message.add_reaction(ctx.message, '\U0000274E')
                    error = await ctx.send(f'Failed to unload module: {type(e).__name__} - {e}')
                    await asyncio.sleep(10)
                    await error.delete()
                else:
                    await discord.Message.add_reaction(ctx.message, '\U00002705')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        """Administrator command."""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            if ctx.channel.id == config['channel_config']['config_channel']:
                try:
                    self.bot.unload_extension(cog)
                    self.bot.load_extension(cog)
                except Exception as e:
                    await discord.Message.add_reaction(ctx.message, '\U0000274E')
                    error = await ctx.send(f'Failed to reload module: {type(e).__name__} - {e}')
                    await asyncio.sleep(10)
                    await error.delete()
                else:
                    await discord.Message.add_reaction(ctx.message, '\U00002705')

    @commands.command(name="build_user_db", hidden=True, aliases=['rebuild_user_db'])
    @commands.is_owner()
    async def build_user_db(self, ctx, member: discord.Member = None):
        """Administrator command"""
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            try:
                if ctx.id == config['channel_config']['config_channel']:
                    pending = await ctx.send(embed=discord.Embed(title='Rebuilding Database...'))
                    if member is None:
                        self.db[str(ctx.guild.id)].drop_collection('users')
                    else:
                        try:
                            self.db[str(ctx.guild.id)]['users'].find_one_and_delete({'_id': member.id})
                        except:
                            pass
                    # pending = await Level.build_level(Level(self.bot), ctx, member, pending)
                    pending = await Profile.build_profile(Profile(self.bot), ctx, member, pending)
                    # pending = await Thank.build_thank(Thank(self.bot), ctx, member, pending)
                    # pending = await Level.build_bday(Level(self.bot), ctx, member, pending)
                    pending = await Starboard.build_sb(Starboard(self.bot), ctx, member, pending)
                    if member is None:
                        await ctx.send(embed=discord.Embed(title='Server Rebuild Complete',
                                                               description=f'Server ID: {str(ctx.guild.id)}'))
                    else:
                        await ctx.send(embed=discord.Embed(title='User Rebuild Complete',
                                                               description=f'User ID: {str(member.id)}'))
                    return
            except:
                if ctx.channel.id == config['channel_config']['config_channel']:
                    pending = await ctx.send(embed=discord.Embed(title='Rebuilding Database...'))
                    if member is None:
                        self.db[str(ctx.guild.id)].drop_collection('users')
                    else:
                        try:
                            self.db[str(ctx.guild.id)]['users'].find_one_and_delete({'_id': member.id})
                        except:
                            pass
                    # pending = await Level.build_level(Level(self.bot), ctx, member, pending)
                    pending = await Profile.build_profile(Profile(self.bot), ctx, member, pending)
                    # pending = await Thank.build_thank(Thank(self.bot), ctx, member, pending)
                    # pending = await Level.build_bday(Level(self.bot), ctx, member, pending)
                    pending = await Starboard.build_sb(Starboard(self.bot), ctx, member, pending)

                    if member is None:
                        await ctx.send(embed=discord.Embed(title='Server Rebuild Complete',
                                                               description=f'Server ID: {str(ctx.guild.id)}'))
                    else:
                        await ctx.send(embed=discord.Embed(title='User Rebuild Complete',
                                                               description=f'User ID: {str(member.id)}'))
    @commands.command(hidden=True)
    @commands.is_owner()
    async def add_to_db(self, ctx):
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            config_channel = self.bot.get_channel(int(config['channel_config']['config_channel']))
        self.server_db = self.db[str(ctx.guild.id)]['users']

        for member in ctx.guild.members:
            if member.bot:
                continue
            user = self.server_db.find_one({'_id': str(member.id)})
            dict = {}
            new_profile = {}
            print(member.name)
            try:
                for platform in user['profile']['aliases']:
                    dict[platform] = user['profile']['aliases'][platform]
                for key in dict:
                    if key in self.sys_aliases.keys():
                        new_profile[key] = dict[key]

                new_profile['dtg'] = None

                profile = {'profile':{'aliases': new_profile, 'wanted_text': user['profile']['wanted_text']}}
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': profile}, upsert=True)
            except KeyError:
                pending = await ctx.send(embed=discord.Embed(title='Rebuilding Database...'))
                pending = await Gold.build_gold(Gold(self.bot), ctx, member, pending)
                pending = await Profile.build_profile(Profile(self.bot), ctx, member, pending)
                pending = await Thank.build_thank(Thank(self.bot), ctx, member, pending)
                pending = await Level.build_bday(Level(self.bot), ctx, member, pending)
                await ctx.send(embed=discord.Embed(title='User Rebuild Complete',
                                                       description=f'User ID: {str(member.id)}'))
            except:
                await ctx.send(f"user caused error, fix their profile after {member.name}, {member.id}")
                continue
        await ctx.send('Done')

def setup(bot):
    bot.add_cog(Master(bot))
