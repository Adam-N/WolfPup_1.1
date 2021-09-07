import json
import os

import discord
from discord.ext import commands
import datetime as dt

from discord.ext.commands import has_permissions

from lib.mongo import Mongo
from lib.util import Util


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None

    @commands.command()
    @commands.guild_only()
    async def joined(self, ctx, member: discord.Member = None):
        """Says when a member joined."""
        if await Util.check_channel(ctx, True):
            if member is None:
                member = ctx.author
            await ctx.send(
                f'{member.display_name} joined at {dt.datetime.strftime(member.joined_at, "%H:%M %b %dth %Y")}.'
                f' That\'s {Util.deltaconv(int((discord.utils.utcnow() - member.joined_at).total_seconds()))}'
                f' ago!')

    @commands.command(name='top_role', aliases=['toprole'])
    @commands.guild_only()
    async def show_toprole(self, ctx, member: discord.Member = None):
        """Simple command which shows the members Top Role."""
        if await Util.check_channel(ctx, True):
            if member is None:
                member = ctx.author
            await ctx.send(f'The top role for {member.display_name} is {member.top_role.name}')

    @commands.command(name='perms', aliases=['check_perms'])
    @commands.guild_only()
    async def check_permissions(self, ctx, member: discord.Member = None):
        """A simple command which checks a members Guild Permissions.
        If member is not provided, the author will be checked."""
        if await Util.check_channel(ctx, True):
            if not member:
                member = ctx.author
            perms = '\n'.join(perm for perm, value in member.guild_permissions if value)
            embed = discord.Embed(title='Permissions for:', description=ctx.guild.name, colour=member.colour)
            embed.set_author(icon_url=member.avatar.url, name=str(member))
            embed.add_field(name='\uFEFF', value=perms)
            await ctx.send(content=None, embed=embed)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def check(self, ctx, member: discord.Member = None):
        if await Util.check_channel(ctx, True):
            if member is None:
                member = ctx.author
            embed = discord.Embed(title=f"{member.name}'s Profile", description="Check this out")
            embed.add_field(name="Joined:",
                            value=f"{Util.deltaconv(int((discord.utils.utcnow() - member.joined_at).total_seconds()))} ago")
            embed.add_field(name="Created on", value=f"{dt.datetime.strftime(member.created_at, '%d %B, %Y  %H:%M')}")
            embed.add_field(name="Username", value=f"{member.name}{member.discriminator}")
            embed.add_field(name="Top role:", value=f"{member.top_role}")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def role_number(self, ctx, *query: discord.Role):
        if await Util.check_channel(ctx, True):
            for i, role in enumerate(query):
                await ctx.send(embed=discord.Embed(title=f'__{str(len(role.members))}__ users in {role.name}'))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        with open(f'config/{before.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        channel = self.bot.get_channel(config['channel_config']['rolepost_channel'])
        if before.roles == after.roles:
            return
        embed = discord.Embed(title=f'{before.name}#{before.discriminator}')
        embed.add_field(name='User:', value=after.mention)
        if set(before.roles) != set(after.roles):
            if len(before.roles) > len(after.roles):
                for role in before.roles:
                    if role not in after.roles:
                        embed.add_field(name='Role change:', value=f'{role.name} removed')
            elif len(before.roles) < len(after.roles):
                for role in after.roles:
                    if role not in before.roles:
                        embed.add_field(name='Role change:', value=f'{role.name} added')
        embed.set_footer(text=f'User ID:{after.id}', icon_url=after.avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        with open(f'config/{payload.guild_id}/config.json', 'r') as f:
            config = json.load(f)
        modlog_channel = self.bot.get_channel(config['channel_config']['modlog_channel'])
        if not payload.cached_message:
            deleted_channel = self.bot.get_channel(payload.channel_id)
            message_id = payload.message_id
            embed = discord.Embed(title='Message Deleted', description='Was not in internal cache. Cannot fetch '
                                                                       'context.')
            embed.add_field(name='Deleted in:', value=deleted_channel.mention)
            embed.add_field(name='Message ID', value=message_id)
            await modlog_channel.send(embed=embed)
            return
        elif payload.cached_message:
            message = payload.cached_message
            if config['prefix'] in message.content[:len(config['prefix'])] or message.author.bot:
                return
            embed = discord.Embed(title='Message Deleted')
            embed.add_field(name='Message Author:', value=message.author.mention)
            embed.add_field(name='Channel:', value=message.channel.mention)
            if len(message.content) > 500:
                msg = message.content
                msg = msg[0:400]
                embed.add_field(name='Message Content:', value=msg)
            else:
                embed.add_field(name='Message Content:', value=message.content)
            embed.set_footer(text=f'Author ID: {message.author.id} | Message ID: {message.id}')
            embed.set_thumbnail(url=message.author.avatar.url)
            await modlog_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        try:
            with open(f'config/{payload.guild_id}/config.json', 'r') as f:
                config = json.load(f)
            modlog_channel = self.bot.get_channel(config['channel_config']['modlog_channel'])
            edited_channel = self.bot.get_channel(payload.channel_id)
            edited_message = await edited_channel.fetch_message(payload.message_id)
            if edited_message.author.bot:
                return
            data = payload.data
            if not payload.cached_message:
                embed = discord.Embed(title='Message Edited. **Not in Internal Cache.**',
                                      description=f'[Jump to message]({edited_message.jump_url})')
                embed.add_field(name='Channel:', value=edited_channel.mention)
                embed.add_field(name='Message Author', value=edited_message.author.mention)
                embed.add_field(name='Edited Message', value=data['content'])
                await modlog_channel.send(embed=embed)
                return
            if payload.cached_message:
                embed = discord.Embed(title='Message Edited',
                                      description=f'[Jump to message]({edited_message.jump_url})')
                embed.add_field(name='Channel:', value=edited_channel.mention)
                embed.add_field(name='User:', value=edited_message.author.mention)
                embed.add_field(name='Message Before:', value=payload.cached_message.content)
                try:
                    embed.add_field(name='Message After:', value=data['content'])
                except KeyError:
                    pass
                embed.set_footer(text=f'User ID: {edited_message.author.id}')
                embed.set_thumbnail(url=edited_message.author.avatar.url)
                await modlog_channel.send(embed=embed)
        except (AttributeError, discord.errors.HTTPException):
            return

    @staticmethod
    async def award_monthly_roles(self, guild):
        if os.path.isfile(f'config/{guild.id}/config.json'):
            with open(f'config/{guild.id}/config.json', 'r') as f:
                config = json.load(f)
            winners = []
            self.server_db = self.db[str(guild.id)]['users']
            channel = self.bot.get_channel(config['channel_config']['config_channel'])
            most_wanted = self.server_db.find().sort('exp', -1)
            most_thanked = self.server_db.find().sort('thanks.thanks_received', -1)
            most_thankful = self.server_db.find().sort('thanks.thanks_given', -1)
            new_embed = discord.Embed(title=f'This Month\'s Ultimate Outlaws!',
                                      description=f'Give it up for this month\'s winners!')
            await channel.send("Starting Monthly Reset")

            for user in most_wanted:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Wanted!', value=f'{winners[0]}')
                    break
            for user in most_thanked:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Thanked!', value=f'{winners[1]}')
                    break
            for user in most_thankful:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Thankful!', value=f'{winners[2]}')
                    break
            await channel.send(embed=new_embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def give_monthly_roles(self, ctx):
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            winners = []
            self.server_db = self.db[str(ctx.guild.id)]['users']
            channel = self.bot.get_channel(config['channel_config']['config_channel'])
            most_wanted = self.server_db.find().sort('exp', -1)
            most_thanked = self.server_db.find().sort('thanks.thanks_received', -1)
            most_thankful = self.server_db.find().sort('thanks.thanks_given', -1)
            new_embed = discord.Embed(title=f'This Month\'s Ultimate Outlaws!',
                                      description=f'Give it up for this month\'s winners!')
            await channel.send("Starting Monthly Reset")
            for user in most_wanted:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Wanted!', value=f'{winners[0]}')
                    break
            for user in most_thanked:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Thanked!', value=f'{winners[1]}')
                    break
            for user in most_thankful:
                user_id = self.bot.get_user(int(user["_id"]))
                if user_id not in winners:
                    winners.append(user_id)
                    new_embed.add_field(name='Most Thankful!', value=f'{winners[2]}')
                    break
            await channel.send(embed=new_embed)




def setup(bot):
    bot.add_cog(Mod(bot))
