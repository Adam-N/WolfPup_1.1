import json

import discord
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None
        self.leaderboards = {'exp': {'exp', 'experience', 'xp'},
                             'thanks.thanks_received': {'thankee', 'thanks received'},
                             'thanks.thanks_given': {'thanker', 'thanks given'}}

    @commands.command(name='leaderboard', aliases=['lb'])
    async def leaderboard(self, ctx, *args):
        async with ctx.channel.typing():
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            await ctx.message.delete()
            self.server_db = self.db[str(ctx.guild.id)]['users']
            leaderboard = None
            if args:
                leaderboard = ' '.join(args)
            if await Util.check_channel(ctx):
                new_embed = discord.Embed(title=f':trophy: __**User Leaderboards**__ :trophy:',
                                          color=discord.Colour.gold())
                new_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
                new_embed.set_footer(text=f'Results provided by: {self.bot.user.name}', icon_url=self.bot.user.avatar.url)
                for stat in self.leaderboards:
                    if leaderboard is not None:
                        if leaderboard in self.leaderboards[stat]:
                            leaderboard = stat
                        else:
                            continue
                    users = self.server_db.find().sort(stat, -1)
                    rank = 1
                    listing, list_user, f_name, user_str = '', '', '', ''
                    stat_1, stat_2, my_stat = None, None, None
                    for user in users:
                        #try:
                        list_user = self.bot.get_user(int(user["_id"]))

                        try:
                            stat_1, stat_2 = stat.split('.')
                        except ValueError:
                            pass
                        if stat_2 is not None:
                            f_name = f'**{stat_2.capitalize().replace("_", " ")}**'
                            user_str = f'`[{str(rank)}.]` *{list_user.name} :* **{user[stat_1][stat_2]}**'
                        else:
                            f_name = f'**{stat.capitalize()}**'
                            user_str = f'`[{str(rank)}.]` *{list_user.name} :* **{user[stat]}**'
                        if list_user == ctx.author:
                            my_stat = user_str
                            user_str = f'**\u27A4** {user_str} '
                        if rank <= 15:
                            listing += f'{user_str}\n'
                            rank += 1
                        '''except (AttributeError, KeyError):
                            config_channel = await self.bot.fetch_channel(config['channel_config']['config_channel'])
                            await config_channel.send(f'Error. {user["_id"]} created the error.')
                            continue'''
                    if my_stat is not None:
                        listing += f'\n__**Your Ranking:**__\n{my_stat}'
                    new_embed.add_field(name=f_name,
                                        value=listing,
                                        inline=True)
                await ctx.send(embed=new_embed)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
