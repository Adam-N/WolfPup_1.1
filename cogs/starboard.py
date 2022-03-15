import asyncio
import os
import json
import discord
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo
import requests


class Starboard(commands.Cog, name='Starboard'):
    def __init__(self, bot):
        self.bot = bot
        self.star_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777605519623585822/11_Discord_icon_4_20.png'
        self.pinned_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777605535801016350/11_Discord_icon_4_80.png'
        self.error_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777606962480807956/11_Discord_icon_2_80.png'
        self.success_url = 'https://cdn.discordapp.com/attachments/767568459939708950/767568508414066739/Status_Indicators12.png'
        self.db = Mongo.init_db(Mongo())
        self.server_db = None
        self.lock = asyncio.Lock()
        self.leaderboards = {"starboard.starred_messages", 'starboard.stars_given', 'starboard.self_starred'}

    @commands.command(name='init_starboard', hidden=True, aliases=['init_sb', 'sb_init'])
    @commands.is_owner()
    async def init_starboard(self, ctx):
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            starboard_config = {
                'starboard_channel': ctx.channel.id,
                'star_react': None,
                'starred_react': None,
                'threshold': 3
            }
            config['starboard_config'] = starboard_config
            with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=2)
            await ctx.send(embed=discord.Embed(title=f'Starboard config initialized'))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        content = False
        self_starred = False
        already_posted = False
        list = None

        try:
            if os.path.isfile(f'config/{payload.guild_id}/config.json'):
                with open(f'config/{payload.guild_id}/config.json', 'r') as f:
                    config = json.load(f)
            channel = self.bot.get_channel(payload.channel_id)
            starboard_channel = self.bot.get_channel(config['starboard_config']['starboard_channel'])
            message = await channel.fetch_message(payload.message_id)
            async with self.lock:
                for react in message.reactions:
                    if react.emoji == config['starboard_config']['star_react']:
                        list = await react.users().flatten()
                        if message.author in list:
                            self_starred = True
                        reaction = react
                        break
            if channel.id != starboard_channel.id:
                self.server_db = self.db[str(payload.guild_id)]['users']
                starboard_db = self.db[str(payload.guild_id)]['starboard']
                url = ""
                test_var = False
                already_posted = discord.utils.get(message.reactions, emoji=config['starboard_config']['starred_react'])
                if payload.emoji.name == config['starboard_config']['star_react']:
                    if reaction.count >= config['starboard_config']['threshold'] and not already_posted:
                        copy_embed = ""
                        if message.embeds:
                            copy_embed = message.embeds[0].to_dict()
                            try:
                                if copy_embed['footer']['text']:
                                    test_var = True
                            except KeyError:
                                pass
                            if message.content and not copy_embed['url']:
                                content = message.content.__add__(f'\n\n**Link Preview:**\n{copy_embed["description"]}')
                            elif message.content and copy_embed['url'] and not test_var:
                                try:
                                    content = " "
                                    url = copy_embed['url']
                                except:
                                    pass
                            else:
                                content = copy_embed["description"]
                                if not content:
                                    content = copy_embed['title']
                            if "fields" in copy_embed:
                                for embeds in message.embeds:
                                    for field in embeds.fields:
                                        content = str(content) + str(f'\n\n**{field.name}**')
                                        content = str(content) + str(f'\n{field.value}')
                        else:
                            content = message.content
                        if channel.type is discord.ChannelType.text:
                            embed = discord.Embed(title=f"{message.author} said...",
                                                  description=f'{content}\n\n[Jump to Message]({message.jump_url})',
                                                  colour=0x784fd7,
                                                  timestamp=message.created_at)
                        elif channel.type is discord.ChannelType.public_thread or channel.type is discord.ChannelType.public_thread:
                            embed = discord.Embed(title=f"{message.author} said...",
                                                  description=f'{content}',
                                                  colour=0x784fd7,
                                                  timestamp=message.created_at)
                        else:
                            embed = discord.Embed(title=f"{message.author} said...",
                                                  description=f'{content}',
                                                  colour=0x784fd7,
                                                  timestamp=message.created_at)

                        embed.set_thumbnail(url=message.author.avatar.url)
                        if message.attachments:
                            embed.set_image(url=message.attachments[0].url)

                        if not self_starred:
                            embed.set_footer(icon_url=self.star_url, text='Original Posted')
                        elif self_starred:
                            embed.set_footer(icon_url=self.star_url, text='Self-Starred')
                            self.server_db.find_one_and_update({'_id': str(payload.member.id)},
                                                               {'$inc': {'starboard.self_starred': 1}})
                        if message.embeds:
                            try:
                                embed.set_image(url=url)
                            except:
                                pass
                        sent = await starboard_channel.send(
                            content=f"> \U00002b50 x{len(list)} **Posted in** {channel.mention} by "
                                    f"{message.author.mention}",
                            embed=embed)
                        list_id = []
                        for member in list:
                            list_id.append(member.id)
                        message_dict = {'message': sent.id, 'star_number': reaction.count,
                                        "author_id": message.author.id, "channel_id": message.channel.id,
                                        "starrers": list_id}
                        starboard_db.find_one_and_update({'_id': str(message.id)},
                                                         {'$set': message_dict}, upsert=True)
                        for guild in self.bot.guilds:
                            react = discord.utils.get(guild.emojis, name=config['starboard_config']['starred_react'])
                        if react is None:
                            react = config['starboard_config']['starred_react']
                        await message.add_reaction(react)

                        for user in list:
                            if user.id != payload.user_id and not user.bot:
                                self.server_db.find_one_and_update({'_id': str(user.id)},
                                                                   {'$inc': {'starboard.stars_given': 1}})

                        self.server_db.find_one_and_update({'_id': str(message.author.id)},
                                                           {'$inc': {'starboard.starred_messages': 1}})

                    elif reaction.count > config['starboard_config']['threshold'] and already_posted:
                        self.server_db = self.db[str(payload.guild_id)]['users']
                        starboard_db = self.db[str(payload.guild_id)]['starboard']
                        star_message = starboard_db.find_one({'_id': str(message.id)})

                        if payload.user_id not in star_message['starrers']:
                            self.server_db.find_one_and_update({'_id': str(payload.user_id)},
                                                               {'$inc': {'starboard.stars_given': 1}})
                            starboard_db.find_one_and_update({'_id': str(message.id)},
                                                             {'$inc': {'star_number': 1}})
                        else:
                            return
                        old_message = await starboard_channel.fetch_message(int(star_message['message']))

                        for react in message.reactions:
                            if react.emoji == config['starboard_config']['star_react']:
                                list = await react.users().flatten()

                        new_content = f"> \U00002b50 x{len(list)}  **Posted in** {channel.mention} by {message.author.mention}"
                        await old_message.edit(content=new_content)

        except KeyError:
            raise KeyError('Starboard settings not initialised')

    @commands.command(aliases=['starleaderboard', 'starleader', 'leaderboard'])
    async def starleaders(self, ctx):
        async with ctx.channel.typing():
            self.server_db = self.db[str(ctx.guild.id)]['users']
            starboard_db = self.db[str(ctx.guild.id)]['starboard']

            if await Util.check_channel(ctx):
                new_embed = discord.Embed(title=f':star: __**User Leaderboards**__ :star:',
                                          color=discord.Colour.gold())
                new_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
                for stat in self.leaderboards:
                    users = self.server_db.find().sort(stat, -1)

                    rank = 1
                    listing, list_user, f_name, user_str = '', '', '', ''
                    stat_1, stat_2, my_stat = None, None, None
                    for user in users:
                        list_user = self.bot.get_user(int(user["_id"]))
                        if list_user is None:
                            continue
                        try:
                            stat_1, stat_2 = stat.split('.')
                        except ValueError:
                            pass
                        if stat_2 is not None:
                            f_name = f'**{stat_2.capitalize().replace("_", " ")}**'
                            user_str = f'`[{str(rank)}.]` *{list_user.display_name} :* **{user[stat_1][stat_2]}**'
                        else:
                            f_name = f'**{stat.capitalize()}**'
                            user_str = f'`[{str(rank)}.]` *{list_user.display_name} :* **{user[stat]}**'

                        if list_user == ctx.author:
                            my_stat = user_str
                            user_str = f'**\u27A4** {user_str} '
                        if rank <= 15:
                            listing += f'{user_str}\n'
                            rank += 1

                    if my_stat is not None:
                        listing += f'\n__**Your Ranking:**__\n{my_stat}'

                    sb_stats = starboard_db.find()
                    star_number = 0
                    for stat in sb_stats:
                        star_number += stat["star_number"]

                    number_of_starred_messages = sb_stats.count()

                    new_embed.set_footer(
                        text=f'{number_of_starred_messages} messages have been starred with {star_number} '
                             f'stars',
                        icon_url=self.bot.user.display_avatar.url)

                    new_embed.add_field(name=f_name,
                                        value=listing,
                                        inline=True)
                await ctx.send(embed=new_embed)

    @commands.command(aliases=['mystats', 'starboardstats', 'stats', 'sbstats'])
    async def my_stats(self, ctx, user: discord.Member = None):
        async with ctx.channel.typing():
            if user is None:
                user = ctx.author
            new_embed = discord.Embed(title=f':star: __**{user.display_name}\'s Starboard Stats**__ :star:',
                                      color=discord.Colour.gold())
            new_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            new_embed.set_footer(text=f'Results provided by: {self.bot.user.name}', icon_url=self.bot.user.display_avatar.url)
            starboard_db = self.db[str(ctx.guild.id)]['starboard']
            self.server_db = self.db[str(ctx.guild.id)]['users']
            stat = 'star_number'
            messages = starboard_db.find().sort(stat, -1)
            user_str = None

            rank = 1
            listing = ''
            for message in messages:
                if message["author_id"] != user.id:
                    continue
                channel = self.bot.get_channel(int(message["channel_id"]))
                message_object = await channel.fetch_message(int(message["_id"]))
                user_str = f'`[{str(rank)}.]` **{user.mention}\'s message in {channel.mention} ' \
                           f' :** {message[stat]} - ' \
                           f'[Click to see message]({message_object.jump_url})'
                if rank <= 3:
                    listing += f'{user_str}\n'
                    rank += 1
            if user_str is None:
                listing = 'No Starred Messages'
            new_embed.add_field(name=f"{user.display_name}\'s Top Starred Messages", value=listing, inline=True)
            user_profile = self.server_db.find_one({"_id": str(user.id)})
            star_info = user_profile['starboard']

            new_embed.add_field(name="Number of Self-Starred Posts:", value=f"{star_info['self_starred']}",
                                inline=False)
            new_embed.add_field(name="Number of Starred Messages:", value=f"{star_info['starred_messages']}",
                                inline=False)
            new_embed.add_field(name="Number of Stars Given:", value=f"{star_info['stars_given']}", inline=False)
            await ctx.send(embed=new_embed)

    @commands.command(aliases=['top_messages', 'moststarred', 'most_starred'])
    async def starmessages(self, ctx):
        async with ctx.channel.typing():
            new_embed = discord.Embed(title=f':star: __**Top Starred Messages**__ :star:',
                                      color=discord.Colour.gold())
            new_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            new_embed.set_footer(text=f'Results provided by: {self.bot.user.name}', icon_url=self.bot.user.display_avatar.url)
            starboard_db = self.db[str(ctx.guild.id)]['starboard']
            if await Util.check_channel(ctx):
                new_embed = discord.Embed(title=f':star: __**Leaderboard**__ :star:',
                                          color=discord.Colour.gold())
                new_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
                stat = 'star_number'
                messages = starboard_db.find().sort(stat, -1)

                rank = 1
                listing, list_message, f_name = '', '', ''
                for message in messages:
                    # try:
                    channel = self.bot.get_channel(int(message["channel_id"]))
                    message_object = await channel.fetch_message(int(message["_id"]))
                    f_name = f'**Top Messages**'
                    user_str = f'`[{str(rank)}.]` *{message_object.author.mention}\'s message in {channel.mention} ' \
                               f' :* **{message[stat]} - ' \
                               f'[Click to see message]({message_object.jump_url})**'
                    if rank <= 5:
                        listing += f'{user_str}\n'
                        rank += 1
                    if len(listing) > 900:
                        break
                new_embed.add_field(name=f_name,
                                    value=listing,
                                    inline=True)
                sb_stats = starboard_db.find()
                star_number = 0
                for stat in sb_stats:
                    star_number += stat["star_number"]

                number_of_starred_messages = sb_stats.count()

                new_embed.set_footer(text=f'{number_of_starred_messages} messages have been starred with {star_number} '
                                          f'stars',
                                     icon_url=self.bot.user.avatar.url)
            await ctx.send(embed=new_embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def add_star_db(self, ctx):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        users = self.server_db.find()
        new_info = {'stars_given': 0, 'starred_messages': 0, 'self_starred': 0}
        for user in users:
            user['starboard'] = new_info
            self.server_db.find_one_and_update({'_id': str(user['_id'])},
                                               {'$set': user})
        await ctx.send('Done')

    @commands.command(hidden=True, name="build_sb")
    @commands.is_owner()
    async def build_sb(self, ctx, member: discord.Member = None, pending=None, dt=None):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding SB stats...'))
        else:
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding SB stats...'))
        if await Util.check_channel(ctx, True):
            new_info = {"starboard": {'stars_given': 0, 'starred_messages': 0, 'self_starred': 0}}
            if member and not member.bot:
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_info}, upsert=True)
                await pending.edit(embed=discord.Embed(title='Done'))
                return
            else:
                for member in ctx.guild.members:
                    if not member.bot:
                        self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_info}, upsert=True)
            await ctx.send(embed=discord.Embed(title='SB Stats Reset'))
            return pending


def setup(bot):
    bot.add_cog(Starboard(bot))
