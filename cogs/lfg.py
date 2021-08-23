import json
import os
import datetime as dt
import discord
from discord.ext import tasks, commands
from discord.errors import NotFound


class LFGCog(commands.Cog, name='lfg'):
    """LFG Rules"""

    def __init__(self, bot):
        self.bot = bot
        self.lfg_message.start()

    def cog_unload(self):
        self.lfg_message.cancel()

    @commands.command()
    @commands.is_owner()
    async def lfg_config(self, ctx):
        lfg_config = {
            'pc_lfg': ctx.channel.id,
            'ps_lfg': ctx.channel.id,
            'xb_lfg': ctx.channel.id,
            'ffxiv_lfg': ctx.channel.id
        }
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
        config['lfg_config'] = lfg_config
        with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
            json.dump(config, f, indent=2)
        await ctx.send(embed=discord.Embed(title=f'LFG config initialized'))

    @tasks.loop(minutes=30)
    async def lfg_message(self):
        guild = self.bot.get_guild(334925467431862272)
        if os.path.isfile(f'config/{guild.id}/config.json'):
            with open(f'config/{guild.id}/config.json', 'r') as f:
                config = json.load(f)

            for lfg in config["lfg_config"]:
                channel = self.bot.get_channel(int(config["lfg_config"][lfg]))

                try:
                    last_message = await channel.fetch_message(channel.last_message_id)
                except NotFound:
                    messages = await channel.history(limit=4).flatten()
                    for message in messages:
                        try:
                            last_message = message
                            break
                        except:
                            continue
                if last_message.author.bot:
                    continue
                if last_message.created_at + dt.timedelta(minutes=90) <= dt.datetime.utcnow():

                    embed = discord.Embed(title="**Welcome to the LFG Channel!**",
                                          description="Here's a few tips to help you get the most out of this "
                                                      "channel and successfully find folks to play with.")

                    embed.add_field(name="**1. Tag Usage**",
                                    value="The best way to draw attention to your LFG is to use the appropriate role "
                                          "tag. This will send a notification directly to folks who are interested in "
                                          "that type of content. Please be patient and allow at least 10-15 minutes "
                                          "for a response before searching through other means or giving the spot "
                                          "away. Please limit yourself to the tag for the content you are looking to "
                                          "play.", inline=False)

                    if 'xiv' in channel.name:
                        tags = []
                        role_string = ", "
                        for role in guild.roles:
                            if "XIV" in role.name and role.name not in ["Final Fantasy XIV", "XIV-Goobues",
                                                                        "XIV-Icepick",
                                                                        "XIV-GITS", "XIV-Pomrangers"]:
                                tags.append(role.mention)
                        role_string = role_string.join(tags)
                        bot_channel = guild.get_channel(586182007852367893)
                        lfg_bot = self.bot.get_user(475744554910351370)
                        embed.add_field(name="**2. Scheduling LFGs**",
                                        value=" We're an adult community so many of our members have limited "
                                              "playtime due to real life responsibilities. Therefore, you can "
                                              "ensure a better turn out for your LFG by planning it in advance "
                                              "and advertising it within this channel. Use `e?event`"
                                              f" in the {bot_channel.mention} and follow "
                                              f"the prompts from {lfg_bot.mention} "
                                              "to create your own interactive LFG!", inline= False)
                        embed.add_field(name="**3. Requirements and Etiquette**",
                                        value="Please respect everyone's time. This means being upfront with any "
                                              "requirements (experienced only, teaching run, etc.), joining an LFG only "
                                              "if you meet the requirements, being punctual or communicating immediately "
                                              "if you'll be late or can't make it, and filling empty spots from the "
                                              "tentative list first before opening them to others.", inline=False)
                        embed.add_field(name="Appropriate Tags:", value=f"{role_string}")


                    elif 'dtg' in channel.name:
                        tags = []
                        role_string = ", "
                        for role in guild.roles:
                            if "D2" in role.name:
                                tags.append(role.mention)
                        role_string = role_string.join(tags)
                        bot_channel = guild.get_channel(515355185363812353)
                        lfg_bot = self.bot.get_user(296023718839451649)
                        embed.add_field(name="**2. Scheduling LFGs**",
                                        value=" We're an adult community so many of our members have limited "
                                              "playtime due to real life responsibilities. Therefore, you can "
                                              "ensure a better turn out for your LFG by planning it in advance "
                                              "and advertising it within this channel. Use `d!lfg create`"
                                              f" in the {bot_channel.mention} and follow "
                                              f"the prompts from {lfg_bot.mention} "
                                              "to create your own interactive LFG!", inline= False)
                        embed.add_field(name="**3. Requirements and Etiquette**",
                                        value="Please respect everyone's time. This means being upfront with any "
                                              "requirements (experienced only, teaching run, etc.), joining an LFG only "
                                              "if you meet the requirements, being punctual or communicating immediately "
                                              "if you'll be late or can't make it, and filling empty spots from the "
                                              "tentative list first before opening them to others.", inline=False)
                        embed.add_field(name="Appropriate Tags:", value=f"{role_string}")

                    elif "pickup" in channel.name:
                        bot_channel = guild.get_channel(511003221817556995)
                        lfg_bot = self.bot.get_user(475744554910351370)
                        embed.add_field(name="**2. Scheduling LFGs**",
                                        value=" We're an adult community so many of our members have limited "
                                              "playtime due to real life responsibilities. Therefore, you can "
                                              "ensure a better turn out for your LFG by planning it in advance "
                                              "and advertising it within this channel. Use e?event"
                                              f" in the {bot_channel.mention} and follow "
                                              f"the prompts from {lfg_bot.mention} "
                                              "to create your own interactive LFG!", inline= False)

                    else:
                        continue


                    try:
                        last_post = await channel.history().find(lambda m: m.author.id == self.bot.user.id)
                        await last_post.delete()
                    except:
                        pass
                    await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(LFGCog(bot))
