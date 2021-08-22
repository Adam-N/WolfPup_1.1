import os
import json
import discord
from discord.ext import commands
from lib.util import Util


class Starboard(commands.Cog, name='Starboard'):
    def __init__(self, bot):
        self.bot = bot
        self.star_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777605519623585822/11_Discord_icon_4_20.png'
        self.pinned_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777605535801016350/11_Discord_icon_4_80.png'
        self.error_url = 'https://cdn.discordapp.com/attachments/767568459939708950/777606962480807956/11_Discord_icon_2_80.png'
        self.success_url = 'https://cdn.discordapp.com/attachments/767568459939708950/767568508414066739/Status_Indicators12.png'

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
        self_starred = False
        try:
            if os.path.isfile(f'config/{payload.guild_id}/config.json'):
                with open(f'config/{payload.guild_id}/config.json', 'r') as f:
                    config = json.load(f)
            channel = self.bot.get_channel(payload.channel_id)
            starboard_channel = self.bot.get_channel(config['starboard_config']['starboard_channel'])
            message = await channel.fetch_message(payload.message_id)
            print(message.attachments)
            print(message.content)
            for react in message.reactions:
                if react.emoji == config['starboard_config']['star_react']:
                    list = await react.users().flatten()
                    if message.author in list:
                        self_starred = True
                    reaction = react
                    break
            if channel.id != starboard_channel.id:
                already_posted = discord.utils.get(message.reactions, emoji=config['starboard_config']['starred_react'])
                if payload.emoji.name == config['starboard_config']['star_react']:
                    if reaction.count >= config['starboard_config']['threshold'] and not already_posted:
                        copy_embed = ""
                        if message.embeds:
                            copy_embed = message.embeds[0].to_dict()

                            if message.content and not copy_embed['url']:
                                content = message.content.__add__(f'\n\n**Link Preview:**\n{copy_embed["description"]}')
                            elif message.content and copy_embed['url']:
                                content = " "
                            else:
                                try:
                                    content = copy_embed["description"]
                                except:
                                    pass
                                if not content:
                                    content = copy_embed['title']

                            if "fields" in copy_embed:
                                for embeds in message.embeds:
                                    for field in embeds.fields:
                                        content = content.__add__(f'\n\n**{field.name}**')
                                        content = content.__add__(f'\n{field.value}')
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
                            raise KeyError('Something went wrong with starboard.')

                        embed.set_thumbnail(url=message.author.avatar.url)
                        if message.embeds:
                            try:
                                if copy_embed['image']:
                                    embed.set_image(url=copy_embed['image']['url'])
                            except:
                                pass
                            try:
                                if copy_embed["video"]:
                                    embed.set_image(url=copy_embed['thumbnail']['url'])
                            except:
                                pass
                            try:
                                if copy_embed["url"]:
                                    embed.set_image(url=copy_embed['url'])
                            except:
                                pass
                        elif message.attachments:
                            embed.set_image(url=message.attachments[0].url)
                        if not self_starred:
                            embed.set_footer(icon_url=self.star_url, text='Original Posted')
                        elif self_starred:
                            embed.set_footer(icon_url=self.star_url, text='Self-Starred')
                        await starboard_channel.send(
                            content=f"> **Posted in** {channel.mention} by {message.author.mention}", embed=embed)
                        for guild in self.bot.guilds:
                            react = discord.utils.get(guild.emojis, name=config['starboard_config']['starred_react'])
                        if react is None:
                            react = config['starboard_config']['starred_react']
                        await message.add_reaction(react)
        except KeyError:
            print('Starboard Settings not Initialized. Skipping reaction check.')
            raise KeyError('Starboard settings not initialised')


def setup(bot):
    bot.add_cog(Starboard(bot))