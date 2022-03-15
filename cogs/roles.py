import json
from lib.mongo import Mongo
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.ext.commands.errors import EmojiNotFound


class RolesCog(commands.Cog, name='roles'):
    """Role Reaction System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = Mongo.init_db(Mongo())
        self.server_db = None

    @commands.command(hidden=True)
    @commands.is_owner()
    async def set_role(self, ctx, role: discord.Role, category: str, name: str, emoji: discord.Emoji = None):
        # Checks the category
        category = category.lower()
        if category not in ['colour', 'color', 'icon', 'destiny', 'ffxiv', 'othergames', 'pronouns']:
            await ctx.send('Category must be: Colour, Color, Icon, Destiny, FFXIV, OtherGames, or Pronouns')
            return

        # Gets DB information and sets the information for the role provided.
        self.server_db = self.db[str(ctx.guild.id)]['roles']
        self.server_db.find_one_and_update({'_id': str(role.id)},
                                           {'$set': {'emoji': emoji.id, 'category': category, 'name': name}},
                                           upsert=True)

        # Sends confirmation
        await ctx.send(f"{role.name} added with {emoji} in {category}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        # When a role is created, a space for it is created in the DB
        self.server_db = self.db[str(role.guild.id)]['roles']
        self.server_db.insert_one({'_id': str(role.id), 'button_id': None,
                                   'emoji': None, 'name': None, 'category': None})

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        # When a role is deleted it's removed from the DB
        self.server_db = self.db[str(role.guild.id)]['roles']
        self.server_db.find_one_and_delete({'_id': str(role.id)})

    @commands.command(hidden=True)
    @commands.is_owner()
    async def build_roles(self, ctx, role: discord.Role = None):
        # Gets DB information
        self.server_db = self.db[str(ctx.guild.id)]['roles']
        # if one role is given it just resets that roles information
        if role is not None:
            self.server_db.find_one_and_update({'_id': str(role.id)}, {"$set": {'button_id': None,
                                                                                'emoji': None, 'name': None,
                                                                                'category': None}})
        # If no role is given, it resets all of the roles in the db.
        else:
            for role in ctx.guild.roles:
                self.server_db.insert_one({'_id': str(role.id), 'button_id': None,
                                           'emoji': None, 'name': None, 'category': None})
        # Confirmation sent
        await ctx.send('Done')

    @commands.command()
    async def list(self, ctx):
        # Gets the select menu information
        view = CategoryDropdownView(self.bot)

        # Sends the message with the SelectMenu attached to it.
        await ctx.send("Which do you want?:", view=view)


class CategoryDropdown(discord.ui.Select):

    def __init__(self, bot):
        self.bot = bot
        # Sets the options for the SelectMenu
        options = [
            discord.SelectOption(label="Destiny", emoji=bot.get_emoji(677647056625729556)),
            discord.SelectOption(label="FFXIV", emoji=bot.get_emoji(677647278420394015)),
            discord.SelectOption(label="Other Games", emoji=bot.get_emoji(869021632499441704)),
            discord.SelectOption(label='Pronouns', emoji=bot.get_emoji(627242047878987786)),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one to the amount of options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder="Pick a Role Category", min_values=1, max_values=len(options), options=options)

    # Callbacks are used for when the interactions are interacted with.
    async def callback(self, interaction: discord.Interaction):
        # We must respond within a set amount of time. Defer allows calculations to happen
        # without a timeout happening. If we want further responses to be ephemeral, this
        # response must include being ephemeral
        await interaction.response.defer(ephemeral=True)
        # Sends typing to show that work is happening.
        async with interaction.channel.typing():
            # Gets data from the menu
            responses = interaction.data
            # Cycles through the information in the SelectMenu
            for label in responses['values']:
                # Since the labels have spaces and capitals, we lower and remove the spaces.
                label = label.lower().replace(" ", "")
                # Gets the new view to send.
                view = ColourDropdownView(self.bot, interaction.guild, label)

                # Have to use followup after using response. It is a webhook.
                await interaction.followup.send(f"Roles for {label}", view=view, ephemeral=True)

                # Waits for the user to respond to the interaction
                await discord.Client.wait_for(self.bot, "interaction", timeout=40)


class CategoryDropdownView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        # Adds the dropdown to our view object.
        self.add_item(CategoryDropdown(bot))


class ColourDropdown(discord.ui.Select, RolesCog):
    def __init__(self, bot, server, category):
        # Blank list to add to
        options = []
        # Gets server info
        self.db = Mongo.init_db(Mongo())

        # Finds all the values that are in the category given.
        roles = self.db[str(server.id)]['roles'].find({"category": category})
        # Iterates over the information found.
        for role in roles:
            # Adds options for the selectmenu using the information from the db.
            options.append(discord.SelectOption(label=f'{server.get_role(int(role["_id"])).name}',
                                                emoji=bot.get_emoji(int(role['emoji'])), value=role['_id']))

        # No max value so the user can select as many options as available.
        super().__init__(placeholder="Pick a Role:", min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Defer response to do calculations
        await interaction.response.defer(ephemeral=True)

        # Get responses
        responses = interaction.data

        # Blank lists to add to later.
        roles_given = []
        roles_taken = []

        # Iterate through the response values.
        for id in responses['values']:
            # Gets role from the server.
            role = interaction.guild.get_role(int(id))

            # Adds the role if the user doesn't have it, removes it if the user does have it.
            if role in interaction.user.roles:
                await interaction.guild.get_member(interaction.user.id).remove_roles(role)
                roles_taken.append(role.name)
            elif role not in interaction.user.roles:
                await interaction.guild.get_member(interaction.user.id).add_roles(role)
                roles_given.append(role.name)

        # Joins the lists to a string
        given = ",".join(roles_given)
        taken = ",".join(roles_taken)

        # Sends a message containing roles given and / or taken.
        await interaction.followup.send(f"{f'You were given {given}.' if len(roles_given) > 0 else ' '} "
                                                f"{f'You had {taken} taken' if len(roles_taken) > 0 else ' '}",
                                                ephemeral=True, delete_after=5)


class ColourDropdownView(discord.ui.View):
    def __init__(self, bot, server, category):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(ColourDropdown(bot, server, category))


def setup(bot):
    bot.add_cog(RolesCog(bot))
