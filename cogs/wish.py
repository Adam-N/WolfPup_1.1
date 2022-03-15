import os
import json
import asyncio
import discord
from discord.ext import commands


class WishWall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefix = ''

    @commands.command(name='init_wish', hidden=True, aliases=['init_iw', 'iw_init'])
    @commands.is_owner()
    async def init_wish(self, ctx):

        # Loads config
        if os.path.isfile(f'config/{ctx.guild.id}/config.json'):
            with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
                config = json.load(f)
            # Builds the configs for the two channels.
            wishwall_xiv = {
                'channel': ctx.channel.id,
                'image': 'https://cdn.discordapp.com/attachments/532380077896237061/786762838789849139/Cid_ARR.jpg',
                'text': 'has requested help!'}

            config['wishwall_xiv'] = wishwall_xiv
            with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=2)

            wishwall_dtg = {
                'channel': ctx.channel.id,
                'image': 'https://media.discordapp.net/attachments/767568459939708950/800966534956318720'
                         '/destiny_icon_grey.png?width=630&height=670',
                'text': 'has made a wish!'}

            # Writes to the config
            config['wishwall_dtg'] = wishwall_dtg
            with open(f'config/{ctx.guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=2)

            # Send confirmation
            await ctx.send(embed=discord.Embed(title=f'Wishwall config initialized'))

    async def build_embed(self, old_embed: discord.Embed = None, author: str = None, description: str = None,
                          id: int = 0,
                          add: discord.Member = None, remove: discord.Member = None,
                          error: bool = False, error_type: int = 0, channel: discord.TextChannel = None):

        # load config
        if os.path.isfile(f'config/{str(channel.guild.id)}/config.json'):
            with open(f'config/{str(channel.guild.id)}/config.json', 'r') as f:
                config = json.load(f)

        # checks channel name to access the right config
        if 'xiv' in channel.name:
            config = config['wishwall_xiv']
        elif 'dtg' in channel.name:
            config = config['wishwall_dtg']
        else:
            raise KeyError('Error with wishwall_config')

        if not error:

            # Checks to see if it needs to edit an embed.
            if old_embed:

                # Builds a new embed from the old embed.
                new_embed = discord.Embed(title=old_embed.title,
                                          description=old_embed.description,
                                          color=old_embed.color)
                new_embed.set_thumbnail(url=config['image'])
                new_embed.set_footer(text=old_embed.footer.text)
                new_embed.timestamp = old_embed.timestamp

                # For adding users to the accepted section.
                if add:
                    # Takes the old list
                    user_list = old_embed.fields[0].value

                    # Adds the user to the list
                    if add.mention not in user_list:
                        user_list = user_list.replace('N/A', '')
                        user_list += '\n' + str(add.mention)

                # For removing users from the accepted section
                elif remove:
                    # Retrieves the old list
                    user_list = old_embed.fields[0].value

                    # Removes the user from the list.
                    if remove.mention in user_list:
                        user_list = user_list.replace(remove.mention, '')

                        # If the list is empty it puts NA in the spot.
                        if len(user_list) == 0:
                            user_list = 'N/A'

                # Adds the user list to the embed.
                new_embed.add_field(name=old_embed.fields[0].name,
                                    value=user_list,
                                    inline=True)

            # checks for an author and description in the embed.
            # If author and description are included, it is a new post.
            if author and description:
                # Builds the new embed.
                new_embed = discord.Embed(title=f'{author} {config["text"]}',
                                          description=f'\"{description}\"',
                                          color=0xff0209)
                new_embed.add_field(name='**Accepted by:**',
                                    value='N/A',
                                    inline=True)
                new_embed.set_thumbnail(url=config['image'])
                new_embed.set_footer(text=f'User ID: {id}')
                new_embed.timestamp = discord.utils.utcnow()
        else:
            # builds a new embed for the error.
            new_embed = discord.Embed(title=f'**Error**',
                                      color=0xff0209)
            if error_type == 1:
                new_embed.description = (f'Configuration for Wishwall is missing or unformatted.\n' +
                                         f'*Please contact staff for assisstance.*')

            elif error_type == 2:
                new_embed.description = (f'Please include a full description of your request.\n' +
                                         f'*{self.prefix}commission* ***<__description__>***')

            else:
                new_embed.description = (f'An unspecified error has occured while executing command.\n' +
                                         f'*Please contact staff for assistance.*')

        # returns the embed that was built.
        return new_embed

    @commands.command(aliases=['comm', 'commission'],
                      description="Use this to make a wish in #xiv-ironworks or #dtg-wishwall")
    async def wish(self, ctx, *args):
        """This command allows you to make a wish for what you would like to do in game!!"""

        # Gets tge prefix and gets the channel
        self.prefix = ctx.prefix
        channel = await self.bot.fetch_channel(ctx.channel.id)
        comm_desc = ' '.join(args)

        # Gets the config.
        if os.path.isfile(f'config/{str(ctx.guild.id)}/config.json'):
            with open(f'config/{str(ctx.guild.id)}/config.json', 'r') as f:
                config = json.load(f)

        # Checks which channel it is posted in.
        if 'xiv' in channel.name:
            config = config['wishwall_xiv']
        elif 'dtg' in channel.name:
            config = config['wishwall_dtg']
        else:
            raise KeyError('Error with wishwall_config')

        # Checks to see if it is posted in the correct channel.
        # Sends an error if it isn't the right channel.
        if channel.id != config['channel']:
            await ctx.send('This command must be used in the correct channel', delete_after=10)
             
            return

        # Checks if it's the right channel.
        elif channel.id == config['channel']:

            # gets the name and id of the author
            comm_owner = ctx.message.author.display_name
            comm_id = ctx.message.author.id

            # Checks if there was a description or not.
            if len(comm_desc) == 0:
                await channel.send(embed=(await self.build_embed(error=True, error_type=2, channel=channel)),
                                   delete_after=5)

            # If there is a description it goes here.
            else:

                # sends the formatted embed.
                # For_thread variable lets the thread be made on that message.
                for_thread = await channel.send(embed=(await self.build_embed(author=comm_owner, description=comm_desc,
                                                                              id=comm_id, channel=channel)),
                                                view=Buttons(self.bot))
                # Threads can't have a name of more than 100 characters.
                if len(comm_desc) >= 100:
                    comm_desc = comm_desc[0:99]

                # Creates the thread.
                # Adds the view
                # Deletes the command
                await for_thread.create_thread(name=comm_desc)
                self.bot.add_view(Buttons(self.bot), message_id=for_thread.id)
                 


class Buttons(discord.ui.View):
    # Needs custom IDs for the views to stay up and work through bot restarts.
    # These are used to build the custom IDs
    custom_id = 0
    custom_id_conf = str(custom_id) + 'a'
    custom_id_decl = str(custom_id) + 'b'

    def __init__(self, bot):
        # Timeout is None so that the view stays up.
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, custom_id=str(custom_id_conf))
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            channel = await self.bot.fetch_channel(channel_id=interaction.message.channel.id)
            message = await channel.fetch_message(interaction.message.id)
            member = await channel.guild.fetch_member(interaction.user.id)

            comm_owner = message.embeds[0].footer.text
            react_user = member.id
            if str(react_user) not in comm_owner:
                await message.edit(
                    embed=(await WishWall.build_embed(WishWall(self.bot), old_embed=message.embeds[0], add=member,
                                                      channel=channel)))
            elif str(react_user) in comm_owner:
                await interaction.response.send_message('You are the owner of this job. You cannot join it',
                                                        ephemeral=True)

            # Make sure to update the message with our updated selves
            try:
                await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                pass
            self.custom_id += 1
            if self.custom_id >= 10000:
                self.custom_id = 1
        except discord.errors.InteractionResponded:
            pass

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.red, custom_id=str(custom_id_decl))
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            channel = await self.bot.fetch_channel(channel_id=interaction.channel_id)
            message = await channel.fetch_message(interaction.message.id)
            member = await channel.guild.fetch_member(interaction.user.id)

            comm_owner = message.embeds[0].footer.text
            react_user = member.id
            if str(react_user) not in message.embeds[0].footer.text and member.mention not in message.embeds[0].fields[
                0].value:
                await interaction.response.send_message(
                    'It appears you are not participating in the job, or the owner of '
                    'it. So you cannot delete or remove yourself from the job.',
                    ephemeral=True)
                return

            await message.edit(embed=(await WishWall.build_embed(WishWall(self.bot), old_embed=message.embeds[0],
                                                                 remove=member, channel=channel)))
            if str(react_user) in message.embeds[0].footer.text:
                await discord.Message.delete(message)
                return

            # Make sure to update the message with our updated selves
            try:
                await interaction.response.edit_message(view=self)
            except discord.errors.NotFound:
                pass
            self.custom_id += 1
            if self.custom_id >= 10000:
                self.custom_id = 1
        except discord.errors.InteractionResponded:
            pass


def setup(bot):
    bot.add_cog(WishWall(bot))
