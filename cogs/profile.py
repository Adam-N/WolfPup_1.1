import io
import asyncio
import discord
from discord import File
from discord.ext import commands
from lib.util import Util
from lib.mongo import Mongo
from PIL import Image, ImageDraw, ImageFont
import requests



class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None
        self.sys_aliases = {'ps': {'ps', 'psn', 'ps4', 'ps5', 'playstation'},
                            'xb': {'xb', 'xb1', 'xbox', 'microsoft'},
                            'steam': {'steam', 'steam64', 'valve'},
                            'ubi': {'uplay', 'ubi', 'ubisoft'},
                            'xiv': {'ffxiv', 'xiv', 'ff'}}

    @commands.command(name='build_profile', hidden=True, aliases=['rebuild_profile'])
    @commands.is_owner()
    async def build_profile(self, ctx, member: discord.Member = None, pending=None):
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if pending:
            await pending.edit(embed=discord.Embed(title='Rebuilding Profile stats...'))
        else:
            pending = await ctx.send(embed=discord.Embed(title='Rebuilding Profile stats...'))
        if await Util.check_channel(ctx, True):
            new_profile = {'profile': {'aliases': {
                           'ps': None, 'xb': None, 'ubi': None, 'steam': None, 'xiv': None},
                           'wanted_text': None}}
            if member:
                self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_profile}, upsert=True)
                return
            for member in ctx.guild.members:
                if not member.bot:
                    self.server_db.find_one_and_update({'_id': str(member.id)}, {'$set': new_profile}, upsert=True)
            await pending.edit(embed=discord.Embed(title='Done'))
            return pending

    @commands.command(name='set', aliases=['add'])
    async def set(self, ctx, system: str, *name: str):
        """Add your usernames for your game system"""
        await ctx.message.delete()
        username = ' '.join(name)
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if await Util.check_channel(ctx, True):
            for platform in self.sys_aliases:
                if system.lower() in self.sys_aliases[platform]:
                    if len(username) > 32:
                        await ctx.send(embed=discord.Embed(title='**[Error]** : Usernames must be 32 characters or less'))
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                       {'$set': {f'profile.aliases.{platform}': username}})
                    await ctx.send(embed=discord.Embed(title='Successfully Updated Profile',
                                                       description=f'**[{platform.upper()}] \u27A4** *{username}*',
                                                       color=discord.Colour.gold()))
                    return
            error = await ctx.send(embed=discord.Embed(title='Error: invalid platform'))
            await asyncio.sleep(5)
            await error.delete()

    @commands.command(name='get')
    async def get(self, ctx, system: str, member: discord.Member = None):
        """Get a users usernames."""
        await ctx.message.delete()
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if await Util.check_channel(ctx):
            if member is None:
                member = ctx.author
            for platform in self.sys_aliases:
                if system.lower() in self.sys_aliases[platform]:
                    user = self.server_db.find({'_id': str(member.id)})
                    for _, user_data in enumerate(user):
                        username = user_data['profile']['aliases'][platform]
                        if username is None:
                            username = 'N/A'
                        await ctx.send(embed=discord.Embed(title=f'*{username}*',
                                                           color=discord.Colour.gold()))
                        return
            error = await ctx.send(embed=discord.Embed(title='Error: invalid platform'))
            await asyncio.sleep(5)
            await error.delete()

    @commands.command(name='search')
    async def search(self, ctx, query, exact_match: bool = False):
        """Search for a user"""
        async with ctx.channel.typing():
            await ctx.message.delete()
            self.server_db = self.db[str(ctx.guild.id)]['users']
            results = []
            count = 0
            if await Util.check_channel(ctx):
                user = self.server_db.find()
                for _, user_data in enumerate(user):
                    for platform in self.sys_aliases:
                        username = user_data['profile']['aliases'][platform]
                        if username is not None:
                            if not exact_match:
                                query = query.lower()
                                username = username.lower()
                            if query in username and user_data['_id'] not in results:
                                count += 1
                                member = await ctx.guild.fetch_member(int(user_data['_id']))
                                results.append(f'`[{str(count)}.]` {member.mention}')
                if len(results) > 0:
                    await ctx.send(embed=discord.Embed(title=f'Found {len(results)} match(es):',
                                                       description='\n'.join(results),
                                                       color=discord.Colour.gold()))
                else:
                    await ctx.send(embed=discord.Embed(title=f'No Matches Found'))

    @commands.command(name='delete', aliases=['del'])
    async def delete(self, ctx, system):
        """Delete a username"""
        await ctx.message.delete()
        self.server_db = self.db[str(ctx.guild.id)]['users']
        if await Util.check_channel(ctx, True):
            for platform in self.sys_aliases:
                if system.lower() in self.sys_aliases[platform]:
                    self.server_db.find_one_and_update({'_id': str(ctx.author.id)},
                                                       {'$set': {f'profile.aliases.{platform}': None}})
                    await ctx.send(embed=discord.Embed(title='Successfully Updated Profile',
                                                       description=f'**[{platform.upper()}] \u27A4** *N/A*',
                                                       color=discord.Colour.gold()))
                    return
            error = await ctx.send(embed=discord.Embed(title='Error: invalid platform'))
            await asyncio.sleep(5)
            await error.delete()

    @commands.command(aliases=['card', 'profilecard', 'canvas'])
    async def profile(self, ctx, member: discord.Member = None):
        """Displays your profile card."""
        async with ctx.channel.typing():
            self.server_db = self.db[str(ctx.guild.id)]['users']
            if await Util.check_channel(ctx):
                if member is None:
                    member = ctx.author
                async with ctx.message.channel.typing():
                    user = self.server_db.find_one({'_id': str(member.id)})
                    bg_img = Image.open('assets/card_to_draw.png').convert('RGBA')
                    ref_img = bg_img.copy()
                    draw = ImageDraw.Draw(ref_img)
                    title_font = ImageFont.truetype('assets/font/NASHVILL.TTF', size=42)
                    text_font = ImageFont.truetype('assets/font/HELLDORA.TTF', size=22)
                    alias_font = ImageFont.truetype('assets/font/libel_suit.ttf', size=20)
                    buffer = 20
                    draw_bounds = [buffer, (ref_img.width-buffer), buffer, (ref_img.height-buffer)]
                    ref_coord = [draw_bounds[0], draw_bounds[2]]
                    # # Title Draw # #
                    text_size = draw.textsize(text='WANTED', font=title_font)
                    draw.text((int((ref_img.width/2)-(text_size[0]/2)), ref_coord[1]),
                              text='WANTED', fill=(16, 16, 16), font=title_font)
                    draw.line((ref_coord[0], ref_coord[1]+int(text_size[1]/2),
                               int(ref_img.width/2)-int(text_size[0]/2+int(buffer/2)), ref_coord[1]+int(text_size[1]/2)),
                              fill=(16, 16, 16), width=5)
                    draw.line((int(ref_img.width/2)+int(text_size[0]/2+int(buffer/2)), ref_coord[1]+int(text_size[1]/2),
                               draw_bounds[1], ref_coord[1]+int(text_size[1]/2)),
                              fill=(16, 16, 16), width=5)
                    draw.line((draw_bounds[0]+buffer, ref_coord[1]+(text_size[1]+int(buffer/2)),
                               draw_bounds[1]-buffer, ref_coord[1]+(text_size[1]+int(buffer/2))),
                              fill=(16, 16, 16), width=5)
                    ref_coord[0] += int(buffer/2)
                    ref_coord[1] += int(text_size[1]+int(buffer*1.5))
                    # # Avatar Draw # #
                    avatar_img = Image.open('assets/gigi_avatar.png')
                    if member.avatar:
                        avatar_img = Image.open(requests.get(member.avatar.url, stream=True).raw).resize((128, 128)).convert('RGBA')
                    emblem_img = Image.open(f'assets/emblem_{user["level"]}.png').convert('RGBA')
                    draw.rectangle((ref_coord[0]-5, ref_coord[1]-5,
                                    ref_coord[0]+avatar_img.width+5, ref_coord[1]+avatar_img.height+5),
                                   fill=(16, 16, 16), width=5)
                    ref_img.paste(avatar_img, (ref_coord[0], ref_coord[1]), avatar_img)
                    ref_img.paste(emblem_img, (int(ref_coord[0]+int(avatar_img.width/2)-int(emblem_img.width/2)),
                                               int(ref_coord[1]+avatar_img.height+1)), emblem_img)
                    ref_coord[0] += avatar_img.width+buffer
                    # # Level/Exp Draw # #
                    x_anchor = ref_coord[0]
                    draw.line((ref_coord[0]-buffer, ref_coord[1]+buffer,
                               draw_bounds[1]-buffer, ref_coord[1]+buffer),
                              fill=(16, 16, 16), width=5)
                    text_size = draw.textsize(text=f'LVL: {user["level"]}', font=text_font)
                    draw.text((ref_coord[0], ref_coord[1]-int(text_size[1]/2)+1),
                              text=f'LVL: {user["level"]}', fill=(32, 32, 32), font=text_font)
                    draw.line((ref_coord[0]+text_size[0]+int(buffer/2), ref_coord[1]-buffer,
                               ref_coord[0]+text_size[0]+int(buffer/2), ref_coord[1]+buffer),
                              fill=(16, 16, 16), width=3)
                    ref_coord[0] += text_size[0]+buffer
                    text_size = draw.textsize(text=f'Bounty: ${user["exp"]}', font=text_font)
                    draw.text((ref_coord[0], ref_coord[1]-int(text_size[1]/2)+1),
                              text=f'Bounty: ${user["exp"]}', fill=(32, 32, 32), font=text_font)
                    # # Alias Draw # #
                    ref_coord[0] = x_anchor
                    ref_coord[1] += int(buffer*1.5)
                    for platform in user['profile']['aliases']:
                        if user['profile']['aliases'][platform] is not None:
                            username = user['profile']['aliases'][platform]
                            if len(username) > 15:
                                try:
                                    first, second = username.split(' ')
                                    username = first+'\n'+second
                                except ValueError:
                                    pass
                            icon_img = Image.open(f'assets/icon/{platform}_logo.png').resize((24, 24)).convert('RGBA')
                            text_size = draw.textsize(text=f'{username}', font=alias_font)
                            sample = icon_img.width+int(buffer/2)+text_size[0]+buffer
                            while sample >= (draw_bounds[1]-x_anchor)/2 or text_size[1] > icon_img.height+5:
                                alias_font = ImageFont.truetype('assets/font/libel_suit.ttf', size=(alias_font.size-1))
                                text_size = draw.multiline_textsize(text=f'{username}', font=alias_font, spacing=1)
                                sample = icon_img.width+int(buffer/2)+text_size[0]+buffer
                            if (ref_coord[0] + sample) > draw_bounds[1]:
                                ref_coord[0] = x_anchor
                                ref_coord[1] += icon_img.height+int(buffer/2)
                            ref_img.paste(icon_img, (ref_coord[0], ref_coord[1]), icon_img)
                            draw.multiline_text((ref_coord[0]+icon_img.width+int(buffer/2), ref_coord[1]-(text_size[1]/2-(icon_img.height/2))),
                                                text=f'{username}', fill=(32, 32, 32), font=alias_font, spacing=1)
                            ref_coord[0] += 117
                    ref_coord[0] = draw_bounds[0]
                    ref_coord[1] = draw_bounds[3]-int(buffer*1.5)+1
                    # # Draw Wanted Text # #
                    text_size = draw.textsize(text='Wanted for', font=text_font)
                    draw.line((ref_coord[0], ref_coord[1], ref_coord[0]+buffer, ref_coord[1]),
                              fill=(16, 16, 16), width=5)
                    draw.text((ref_coord[0]+buffer+2, ref_coord[1]-(text_size[1]/2)),
                              text='Wanted for', fill=(16, 16, 16), font=text_font)
                    draw.line((ref_coord[0]+text_size[0]+buffer+1, ref_coord[1], draw_bounds[1]-(buffer*2.5), ref_coord[1]),
                              fill=(16, 16, 16), width=5)
                    wanted_text = user['profile']['wanted_text']
                    if wanted_text is None:
                        wanted_text = 'Shootin\', lootin\', and rootin\' tootin\' degeneracy'
                    text_font = ImageFont.truetype('assets/font/libel_suit.ttf', size=19)
                    text_size = draw.textsize(text=wanted_text, font=text_font)
                    draw.text((ref_coord[0]+int(buffer/4), ref_coord[1]+text_size[1]-2),
                              text=wanted_text, fill=(48, 48, 48), font=text_font)
                    # Send finished image
                    send_buffer = io.BytesIO()
                    ref_img.save(send_buffer, format='PNG')
                    send_buffer.seek(0)
                    await ctx.message.delete()
                    await ctx.send(file=File(send_buffer, 'myimage.png'))

    @commands.command(name='wanted')
    async def wanted(self, ctx, *text):
        """Sets the custom wanted text on your profile card. """
        await ctx.message.delete()
        self.server_db = self.db[str(ctx.guild.id)]['users']
        wanted = ' '.join(text)
        if await Util.check_channel(ctx, True):
            if len(wanted) != 0:
                if len(wanted) > 50:
                    await ctx.send(embed=discord.Embed(title='**[Error]** : Wanted Text must be 50 characters or less'))
                    return
                self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$set': {f'profile.wanted_text': wanted}})
                await ctx.send(embed=discord.Embed(title='Successfully Updated Wanted Text:',
                                                   description=f'*{wanted}*'))
            else:
                self.server_db.find_one_and_update({'_id': str(ctx.author.id)}, {'$set': {f'profile.wanted_text': None}})
                await ctx.send(embed=discord.Embed(title='Successfully set Wanted Text to Default'))


def setup(bot):
    bot.add_cog(Profile(bot))
