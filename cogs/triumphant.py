import os
import json
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from lib.mongo import Mongo
from discord.errors import Forbidden


class Triumphant(commands.Cog, name='Triumphant'):
    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None
        self.sys_aliases = {'ps': {'ps', 'psn', 'ps4', 'ps5', 'playstation'},
                            'xb': {'xb', 'xb1', 'xbox', 'microsoft'},
                            'steam': {'steam', 'steam64', 'valve'},
                            'ubi': {'uplay', 'ubi', 'ubisoft'},
                            'xiv': {'ffxiv', 'xiv', 'ff'}}

    @commands.command(name='init_triumphant', hidden=True)
    @commands.is_owner()
    async def init_triumphant(self, ctx):
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            triumphant_config = {
                'triumph_channel': ctx.channel.id,
                'triumph_react': None
            }
            config['triumphant_config'] = triumphant_config
            with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=2)
            await ctx.send(embed=discord.Embed(title=f'Triumphant config initialized'))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        if os.path.isfile(f'config/{str(payload.guild_id)}/config.json'):
            with open(f'config/{str(payload.guild_id)}/config.json', 'r') as f:
                config = json.load(f)

        if str(payload.emoji) not in config['triumphant_config']['triumph_react']:
            return
        self.server_db = self.db[str(payload.guild_id)]['users']
        guild = self.bot.get_guild(payload.guild_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        not_bot_user = None
        id_list = []
        name_list = []
        posting_channel = await self.bot.fetch_channel(int(config['triumphant_config']["triumph_channel"]))
        for reaction in msg.reactions:
            async for user in reaction.users():
                if user.id == self.bot.user.id and str(payload.emoji) in config['triumphant_config']['triumph_react']:
                    return
        try:
            await msg.add_reaction(config['triumphant_config']['triumph_react'])
        except Forbidden:
            pass
        results = []
        count = 0
        if msg.embeds:
            copy_embed = msg.embeds[0].to_dict()
            for member in guild.members:
                if member.bot:
                    continue
                if member.name.lower() in copy_embed['description'].lower() or \
                        member.display_name.lower() in copy_embed['description'].lower():
                    not_bot_user = member.id
                    break
            if not not_bot_user:
                user = self.server_db.find()
                for _, user_data in enumerate(user):
                    try:
                        for platform in self.sys_aliases:
                            username = user_data['profile']['aliases'][platform]
                            if username is not None:
                                try:
                                    if username.lower() in copy_embed['description'].lower() and user_data['_id'] not in results:
                                        results.append(user_data['_id'])
                                        not_bot_user = int(user_data['_id'])
                                        break
                                except KeyError:
                                    break
                        if user_data['_id'] in results:
                            break
                    except KeyError:
                        break

            copy_embed = msg.embeds[0].to_dict()
            if msg.content:
                try:
                    content = msg.content.__add__(f'\n\n**Link Preview:**\n{copy_embed["description"]}')
                except KeyError:
                    try:
                        content = msg.content.__add__(f'\n\n**Link Preview:**\n{copy_embed["title"]}')
                    except KeyError:
                        pass
                    pass
            else:
                try:
                    content = copy_embed["description"]
                except KeyError:
                    content = copy_embed["title"]
            if "fields" in copy_embed:
                for embeds in msg.embeds:
                    try:
                        for field in embeds.fields:
                            content = content.__add__(f'\n\n**{field.name}**')
                            content = content.__add__(f'\n{field.value}')
                    except:
                        continue
        else:
            content = msg.content
        if msg.mentions:
            for member in msg.mentions:
                id_list.append(str(member.id))
                name_list.append(str(member.name))
        embed = discord.Embed(title=f"{msg.author} said...",
                              description=f'{content}\n\n[Jump to Message](https://discordapp.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id})',
                              colour=0x784fd7,
                              timestamp=msg.created_at)
        if id_list:
            name_string = "\n".join(name_list)
            id_string = "\n".join(id_list)

            embed.add_field(name="People mentioned in the message:", value=name_string)
            embed.add_field(name="IDs:", value=id_string)
        if not msg.author.bot:
            embed.set_footer(text=f"ID:{msg.author.id}")
            try:
                embed.set_thumbnail(url=msg.author.avatar.url)
            except TypeError:
                pass
            embed.add_field(name="Nominated User:", value=f"{msg.author.name}")
        if msg.author.bot:
            if not_bot_user:
                embed.set_footer(text=f"ID:{not_bot_user}")
                avatar_member = await guild.fetch_member(not_bot_user)
                embed.set_thumbnail(url=avatar_member.avatar.url)
                embed.add_field(name="Nominated User:", value=f"{avatar_member.name}")
        if msg.embeds:
            if "image" in copy_embed:
                embed.set_image(url=copy_embed["image"]["url"])
            elif "video" in copy_embed:
                embed.set_image(url=copy_embed["thumbnail"]["url"])
        elif msg.attachments:
            embed.set_image(url=msg.attachments[0].url)
        embed.add_field(name='Nominated by:', value=f'{payload.member.name}')
        await posting_channel.send(embed=embed)
        if os.path.isfile(f'config/{payload.guild_id}/triumphant.json'):
            with open(f'config/{payload.guild_id}/triumphant.json', 'r') as f:
                users = json.load(f)
        else:
            users = {}
        if not msg.author.bot:
            users[str(msg.author.id)] = 1
        if msg.author.bot and not_bot_user:
            users[str(not_bot_user)] = 1
        if msg.mentions:
            for member in id_list:
                users[str(member)] = 1
        with open(f'config/{payload.guild_id}/triumphant.json', 'w') as f:
            json.dump(users, f)

    @commands.command(hidden=True)
    @has_permissions(manage_messages=True)
    async def triumph_delete(self, ctx, member_id: int):
        try:
            member = await ctx.guild.fetch_member(member_id)
            with open(f'config/{ctx.guild.id}/triumphant.json', 'r') as f:
                users = json.load(f)
            try:
                if users[str(member_id)] == 1:
                    del users[str(member_id)]
            except:
                del_embed = discord.Embed(title='User was not in the list')
                del_embed.add_field(name="User:", value=f"{member.name}")
                del_embed.add_field(name="User Id:", value=f"{member_id}")
                await ctx.send(embed=del_embed)
                return
        except:
            with open(f'config/{ctx.guild.id}/triumphant.json', 'r') as f:
                users = json.load(f)
            try:
                if users[str(member_id)] == 1:
                    del users[str(member_id)]
            except:
                await ctx.send('User not in DB.')
                return
        with open(f'config/{ctx.guild.id}/triumphant.json', 'w+') as f:
            json.dump(users, f)
        await ctx.send(f"Succesfully deleted {member.name} from triumphant list. ID: {member_id}")

    @commands.command(hidden=True)
    @has_permissions(manage_messages=True)
    async def triumph_add(self, ctx, member_id: int):
        member = await ctx.guild.fetch_member(member_id)
        with open(f'config/{ctx.guild.id}/triumphant.json', 'r') as f:
            users = json.load(f)

        try:
            if users[str(member_id)]:
                add_embed = discord.Embed(title='User was already triumphant')
                add_embed.add_field(name="User:", value=f"{member.name}")
                add_embed.add_field(name="User Id:", value=f"{member_id}")
                await ctx.send(embed=add_embed)
                return
        except:
            users[str(member_id)] = 1

        with open(f'config/{ctx.guild.id}/triumphant.json', 'w') as f:
            json.dump(users, f)

        add_embed = discord.Embed(title='User is now triumphant')
        add_embed.add_field(name="User:", value=f"{member.name}")
        add_embed.add_field(name="User Id:", value=f"{member_id}")
        await ctx.send(embed=add_embed)

    @commands.command(hidden=True)
    @has_permissions(manage_messages=True)
    async def triumph_list(self, ctx, copy: str = None):
        id_list = ''
        user_list = ''

        if copy is None:
            with open(f'config/{ctx.guild.id}/triumphant.json', 'r') as f:
                users = json.load(f)
                copy = ""
        if copy:
            with open(f'config/{ctx.guild.id}/triumphant_copy.json', 'r') as f:
                users = json.load(f)

        for key in users:
            try:
                member = await ctx.guild.fetch_member(member_id=int(key))
                user_list = user_list + str(member.name) + " \n"
                id_list = id_list + key + " \n"
            except:
                continue
        list_embed = discord.Embed(title=f'Members on the triumphant list {copy}')
        list_embed.add_field(name='List:', value=f"{user_list}")
        list_embed.add_field(name="IDs:", value=f"{id_list}")
        await ctx.send(embed=list_embed)

    @commands.command(aliases=["give_triumph", "triumph_give"],hidden=True)
    @has_permissions(manage_messages=True)
    async def give_triumphant(self, ctx):
        async with ctx.channel.typing():
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            triumphant_role = ctx.guild.get_role(int(config['role_config']["triumphant"]))

            current_triumphant = list(triumphant_role.members)
            member_list = ""
            triumph_embed = discord.Embed(title="Triumphant Role Success",
                                          description="These users have received their role.")

            with open(f'config/{ctx.guild.id}/triumphant_copy.json', 'r') as f:
                users = json.load(f)

            for member in current_triumphant:
                await member.remove_roles(triumphant_role)

            for key in users:
                try:
                    user = ctx.channel.guild.get_member(user_id=int(key))
                    member_list = member_list + user.name + '\n'
                    await user.add_roles(triumphant_role)
                except AttributeError:
                    continue

            os.remove(f'config/{ctx.guild.id}/triumphant_copy.json')


            triumph_embed.add_field(name="Users:", value=f"{member_list}")
            await ctx.send(embed=triumph_embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def manual_reset(self, ctx):
        async with ctx.channel.typing():

            if os.path.isfile(f'config/{ctx.guild.id}/triumphant_copy.json'):
                return
            elif not os.path.isfile(f'config/{ctx.guild.id}/triumphant_copy.json') and os.path.isfile(
                    f'config/{ctx.guild.id}/triumphant.json'):
                with open(f'config/{ctx.guild.id}/triumphant.json', 'r') as f:
                    users = json.load(f)
                with open(f'config/{ctx.guild.id}/triumphant_copy.json', 'w') as f:
                    json.dump(users, f)

                os.remove(f'config/{ctx.guild.id}/triumphant.json')

                triumphant = {}

                with open(f'config/{str(ctx.guild.id)}/triumphant.json', 'w') as f:
                    json.dump(triumphant, f)

                reset_embed = discord.Embed(title="\U0001f5d3| New Week Starts Here. Get that bread!")
                with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                    config = json.load(f)
                chan = self.bot.get_channel(int(config['triumphant_config']["triumph_channel"]))

                await chan.send(embed=reset_embed)

def setup(bot):
    bot.add_cog(Triumphant(bot))
