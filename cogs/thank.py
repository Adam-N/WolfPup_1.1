import random
import discord
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo
from cogs.level import Level


class Thank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None

    @commands.command(name='build_thank', hidden=True, aliases=['rebuild_thank'])
    @commands.is_owner()
    async def build_thank(self, ctx, member: discord.Member = None, pending=None):
        # Gets DB
        self.server_db = self.db[str(ctx.guild.id)]['users']

        # Pending is used when using a more upstream command.
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding Thank stats...'))
        else:
            # If no pending, it makes it's own embed to edit later.
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding Thank stats...'))

        # Checks if it is a bot channel
        if await Util.check_channel(ctx, True):
            new_thank = {'thanks': {'thanks_received': 0, 'total_received': 0,
                                    'thanks_given': 0, 'total_given': 0}}
            # If it is a member it only rebuilds that members thanks.
            if member and not member.bot:
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_thank}, upsert=True)
                await pending.edit(embed=discord.Embed(title='Done'))
                return

            # If no member is specified it builds for the whole server.
            for member in ctx.guild.members:
                if not member.bot:
                    self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_thank}, upsert=True)
            await pending.edit(embed=discord.Embed(title='Thank Stats Reset'))
            return pending

    @commands.command(name='thank', aliases=['thanks'])
    async def thank(self, ctx, member: discord.Member, *args):
        if not member:
            ctx.send('Please properly tag a user', delete_after=5)
            raise TypeError('Error Finding User')
        # Finds the DB
        self.server_db = self.db[str(ctx.guild.id)]['users']

        # Creates the reason for thanking, or builds it based on the user input
        reason = 'For being such a great person!'
        if args:
            reason = ' '.join(args)

        # Checks if it is a bot channel.
        if await Util.check_channel(ctx, False):
            if not member.bot:

                # Gets user information from DB
                user = self.server_db.find_one({'_id': str(ctx.author.id)})

                # Checks to see if the user has used thank yet today.
                if user['flags']['thank']:

                    if ctx.author == member:
                        new_embed = discord.Embed(title='\U0001f441\U0001f441 You tried to thank yourself,'
                                                        ' shame on you \U0001f441\U0001f441')
                        shame_gifs = ['https://media.giphy.com/media/NSTS6t7qKTiDu/giphy.gif',
                                      'https://media.giphy.com/media/vX9WcCiWwUF7G/giphy.gif',
                                      'https://media.giphy.com/media/eP1fobjusSbu/giphy.gif',
                                      'https://media.giphy.com/media/Db3OfoegpwajK/giphy.gif',
                                      'https://media.giphy.com/media/8UGoOaR1lA1uaAN892/giphy.gif']
                        new_embed.set_image(url=random.choice(shame_gifs))
                        await ctx.send(embed=new_embed)
                        return

                    # builds the embed to send.
                    new_embed = discord.Embed(title=f'\U0001f49d {ctx.author.display_name}'
                                                    f' *has thanked* {member.display_name} \U0001f49d',
                                              description=f'*{reason}*',
                                              color=discord.Colour.gold())
                    await ctx.send(embed=new_embed)

                    # Finds thanker and thankee DB info and updates it and adds experience.
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$set': {'flags.thank': False}})
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$inc': {'thanks.thanks_given': 1,
                                                                                              'thanks.total_given': 1}})
                    await Level.update_experience(Level(self.bot), str(ctx.guild.id), str(ctx.author.id),
                                                  random.randint(450, 550))
                    self.server_db.find_one_and_update({'_id': str(member.id)}, {'$inc': {'thanks.thanks_received': 1,
                                                                                          'thanks.total_received': 1}})
                    await Level.update_experience(Level(self.bot), str(ctx.guild.id), str(member.id),
                                                  random.randint(850, 1150))
                else:
                    # Seends this embed if someone has already thanked today.
                    await ctx.send(embed=discord.Embed(
                        title=':broken_heart: You\'ve already thanked someone today! :broken_heart:',
                        description='*Sorry, but you can give another thank tomorrow!*',
                        color=discord.Colour.gold()))

    @commands.command(name='my_thanks')
    async def my_thanks(self, ctx):
        await ctx.message.delete()
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if await Util.check_channel(ctx, True):
            user = self.server_db.find_one({'_id': str(ctx.author.id)})
            new_embed = discord.Embed(title=f'{ctx.author.display_name}\'s Stats',
                                      color=discord.Colour.gold())
            for stat in user['thanks']:
                new_embed.add_field(name=f'**{str(stat).capitalize().replace("_", " ")}** :',
                                    value=f'{user["thanks"][str(stat)]}',
                                    inline=True)
            await ctx.send(embed=new_embed)


def setup(bot):
    bot.add_cog(Thank(bot))
