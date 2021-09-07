import random

import discord
from discord.ext import commands


class Friend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='nomean', aliases=['yesmean'], description="For a friend who's being mean to themself!")
    async def nomean(self, ctx):
        """This command is for a friend who is being mean to themselves.
        Show them who's boss and cheer them up!"""
        embed = discord.Embed(color=0x00ff00)
        embed.title = "Don't be mean to yourself"
        embed.description = 'This is because we love you'
        embed.set_image(
            url='https://cdn.discordapp.com/attachments/532380077896237061/791855065111592970/20200928_123113.jpg')
        await ctx.channel.send(embed=embed)

    @commands.command(name='nosuck', description="For friend's who think they suck.")
    async def nosuck(self, ctx):
        """This command will make your friend think twice about saying that they suck! (In a good way!"""
        embed = discord.Embed(color=0x00ff00)
        embed.title = "Don't be mean to yourself"
        embed.description = 'This is because we love you'
        embed.set_image(
            url='https://cdn.discordapp.com/attachments/532380077896237061/791855064804753418/fql8g0wcp1o51.jpg')
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=['hornyjail', 'nohorny', 'horny', 'yeshorny'],
                      description="For someone who's getting a little lewd.")
    async def horny_jail(self, ctx):
        """This command is meant for that certain friend who's started themselves down the path of sin. UwU"""
        images = ["https://media.tenor.com/images/f781d9b1bbc4839dff9ad763c28deb46/tenor.gif",
                  "https://media1.tenor.com/images/6493bee2be7ae168a5ef7a68cf751868/tenor.gif?itemid=17298755",
                  "https://media.discordapp.net/attachments/767568459939708950/807751886278492170/no_horny.gif"]
        url = random.choice(images)
        embed = discord.Embed(color=0x00ff00)
        embed.title = "You're gross."
        embed.description = 'This is for your own good'
        embed.set_image(url=url)
        await ctx.channel.send(embed=embed)

    @commands.command(description="For someone who needs sleep!")
    async def sleep(self, ctx, member: discord.Member = None):
        """This command is meant to tell a friend to go to sleep!"""
        name = ""
        images = ["https://media1.tenor.com/images/f3fd2914f8db39338263dc7b657bcb43/tenor.gif?itemid=5219925",
                  "https://media1.tenor.com/images/5fb8a2a7db6ce0715013d870631ab81f/tenor.gif?itemid=6146952",
                  "https://media1.tenor.com/images/0e19c69eb1d0e6d58f1c8418b8232881/tenor.gif?itemid=15301397",
                  "https://media.tenor.com/images/11baf16c4029abc97bdae7ff3f6ffe3b/tenor.gif",
                  "https://media.giphy.com/media/rvxGjhW3TKVeo/source.gif",
                  "https://i.gifer.com/RLil.gif",
                  "https://i.imgur.com/juYkVr8.jpg",
                  "https://cdn.discordapp.com/attachments/586181879611260928/850529213000712233/tenor.gif"]
        url = random.choice(images)
        embed = discord.Embed(color=0x00ff00)
        if member is not None:
            if member.nick:
                name = " " + member.nick

            else:
                name = " " + member.display_name
        embed.title = f"Go to sleep{name}!"
        embed.description = 'This is for your own good'
        embed.set_image(url=url)
        await ctx.channel.send(embed=embed)

    @commands.command(description="For someone who needs sleep!")
    async def terry(self, ctx):
        """Terry Command"""
        name = ""
        images = ["https://i.imgur.com/rq4Om02.jpg", "https://i.imgur.com/9c5GchZ.jpg",
                  "https://i.imgur.com/9c5GchZ.jpg", "https://i.imgur.com/4XYABRg.jpg",
                  "https://i.imgur.com/VK0vDv8.jpg", "https://i.imgur.com/C4p4pmN.jpg",
                  "https://i.imgur.com/AcwdkGU.jpg", "https://i.imgur.com/yiYEgmu.png",
                  "https://i.imgur.com/8Wu8voN.jpg", "https://i.imgur.com/81e3EGg.jpg",
                  "https://i.imgur.com/5hnKRzL.jpg", "https://i.imgur.com/zpYv6fT.jpg",
                  "https://i.imgur.com/W5Pg7d3.png", "https://i.imgur.com/o14epCZ.png",
                  "https://i.imgur.com/5YkAqrs.png", "https://i.imgur.com/sTFehUh.jpg",
                  "https://i.imgur.com/MJu4EVZ.png", "https://i.imgur.com/XUTsIDg.png",
                  "https://i.imgur.com/OjjwX4h.jpg", "https://i.imgur.com/2ITAMQ4.jpg"]
        url = random.choice(images)
        embed = discord.Embed(color=0x00ff00)

        embed.title = f"You have summoned the one true god of thumbs!"
        embed.description = ' '
        embed.set_image(url=url)
        await ctx.channel.send(embed=embed)

    @commands.command(name="sherpa", aliases=['Sherpa'])
    async def sherpa(self, ctx):
        await ctx.send(
            'https://docs.google.com/document/d/1NSvJ5KsutXBTnjXfL2BgTi-Z7p4EdqXfruAQEtb32VU/edit?usp=sharing')

    @commands.command(name='credits')
    async def credits(self, ctx):
        embed = discord.Embed(title='Development Credits',
                              description='Thank you to all of the following folks for making Gigi possible.',
                              colour=0xffff33)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name='Developers', value='ShiinaBat#8227\nAdam.M#9788\nInf_Wolf14#7391', inline=True)
        embed.add_field(name='Producers', value='Element#1337\nIlyesia#8008')
        embed.add_field(name='Alpha Testers',
                        value='AzureEiyu#9781, Isaac2K#1948, Kurokaito#5489, Vyxea#0001',
                        inline=False)
        embed.add_field(name='Character Designer',
                        value='[NEBULArobo](https://nebularobo.carrd.co/)', inline=False)
        embed.add_field(name='Icon Artist',
                        value='[crankiereddy](https://twitter.com/crankiereddy)',
                        inline=False)
        await ctx.send(content=None, embed=embed)

def setup(bot):
    bot.add_cog(Friend(bot))
