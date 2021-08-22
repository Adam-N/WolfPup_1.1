import json
import random
import discord
from discord.ext import commands
from lib.util import Util
import datetime as dt
from master import Master


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_count = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open(f'config/{member.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = self.bot.get_channel(config['channel_config']['welcome_channel'])
        welcome_embed = discord.Embed(title="Member joined", description=f'{member.name} has joined.')
        welcome_embed.add_field(name="ID:", value=f"{member.id}", inline=True)
        created = discord.utils.utcnow() - member.created_at
        welcome_embed.add_field(name="Created:",
                              value=f"{Util.deltaconv(int(created.total_seconds()))} ago")
        welcome_embed.set_thumbnail(url=member.avatar.url)
        welcome_embed.timestamp = discord.utils.utcnow()
        i = 0
        if not self.bot_count:
            for member in member.guild.members:
                if member.bot:
                    i += 1
            self.bot_count = i
        elif self.bot_count:
            i = self.bot_count
        total = member.guild.member_count
        welcome_embed.add_field(name="Join number: ", value=f"{total - i}", inline=True)
        await config_channel.send(embed=welcome_embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        with open(f'config/{before.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        role = before.guild.get_role(config['role_config']['posse'])
        welcome_channel = self.bot.get_channel(config['channel_config']['lounge'])

        if role not in before.roles and role in after.roles and before.joined_at > discord.utils.utcnow() - dt.timedelta(minutes=20):
            ment = after.mention
            welcome_messages = [
                f"\U0001f4e2 \U0000269f Say hello to {ment}!",
                f"\U0001f4e2 \U0000269f Hello there! ~~General Kenobi~~ {ment}!!",
                f"\U0001f4e2 \U0000269f A wild {ment} appeared.",
                f"\U0001f4e2 \U0000269f Everyone welcome, {ment}",
                f"\U0001f4e2 \U0000269f Welcome, {ment}! We hope you brought pizza.",
                f"\U0001f4e2 \U0000269f Brace yourselves. {ment} is here!",
                f"\U0001f4e2 \U0000269f {ment} is here, as the prophecy foretold.",
                f"\U0001f4e2 \U0000269f Hey! Listen! {ment} has joined!",
                f"\U0001f4e2 \U0000269f {ment} is near.",
                f"\U0001f4e2 \U0000269f {ment} joined your party.",
                f"\U0001f4e2 \U0000269f {ment} is breaching the wall on the north side. Give them all you got!",
                f"\U0001f4e2 \U0000269f Welcome ~~Tenno~~ {ment}!",
                f"\U0001f4e2 \U0000269f {ment} just arrived. Seems OP - please nerf.",
                f"\U0001f4e2 \U0000269f {ment} joined. You must construct additional pylons.",
                f"\U0001f4e2 \U0000269f ~~**Tactical nuke**~~ {ment}, incoming!🚨"
            ]
            await welcome_channel.send(random.choice(welcome_messages))
            config_channel = self.bot.get_channel(int(config['channel_config']['config_channel']))
            await Master.build_user_db(config_channel, after)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with open(f'config/{member.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        config_channel = self.bot.get_channel(config['channel_config']['welcome_channel'])
        leave_embed = discord.Embed(title="Member left", description=f'{member.name} has left')
        if member.nick:
            leave_embed.add_field(name="Nick: ", value=f"{member.nick}", inline=True)
        leave_embed.add_field(name="ID:", value=f"{member.id}", inline=True)
        joined = discord.utils.utcnow() - member.joined_at

        leave_embed.add_field(name="Joined",
                              value=f"{Util.deltaconv(int(joined.total_seconds()))} ago")
        mentions = [role.mention for role in member.roles if role.name != '@everyone']
        if not mentions:
            mentions = 'N/A'
        leave_embed.add_field(name="Roles:", value=" ".join(mentions))
        leave_embed.set_thumbnail(url=member.avatar.url)
        leave_embed.timestamp = discord.utils.utcnow()
        await config_channel.send(embed=leave_embed)


def setup(bot):
    bot.add_cog(Welcome(bot))
