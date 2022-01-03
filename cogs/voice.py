from discord.ext import commands
import discord
import json


class Voice(commands.Cog, name="Voice"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def make_channel(self, ctx, *args):
        # Checks channel name
        if not args:
            return await ctx.send('You need to specify a channel name.')

        # Makes sure that the user is in a voice channel
        voice_state = ctx.author.voice
        if voice_state is None:
            return await ctx.send('You need to be in a voice channel to use this command')

        # Builds channel name.
        channel_name = ' '.join(args)
        channel_name = f"[GIGI] {channel_name}"
        if len(channel_name) > 100:
            channel_name = channel_name[:100]

        # Gets category and creates the channel in that category
        category = voice_state.channel.category
        new_channel = await category.create_voice_channel(channel_name)
        await ctx.author.move_to(new_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:

            if after.channel.id
        # Try and Except is because if the user is not in a channel before it throws an error.
        try:
            # Checks for the string used in Gigi created channels.
            if "[GIGI]" in before.channel.name:
                # If no members it deletes the channel.
                if not before.channel.members:
                    await before.channel.delete()
        except AttributeError:
            pass

    @commands.command(hidden=True)
    # @commands.has_permissions(move_members=True)
    async def moveplayer(self, ctx, user: discord.Member):
        voice_state = ctx.author.voice
        if voice_state is None:
            return await ctx.send('You need to be in a voice channel to use this command')
        elif user.voice is None:
            return await ctx.send('The person you are trying to move must be in a voice channel.')
        elif voice_state.channel == user.voice.channel:
            return await ctx.send('That user is already in a channel with you.')
        user_channel = user.voice.channel
        voiceChannel = voice_state.channel
        await user.move_to(voiceChannel)

        new_embed = discord.Embed(title="**User Moved**", description=f"{ctx.author.display_name} moved "
                                                                      f"{user.display_name} from {user_channel.name} "
                                                                      f"to {voiceChannel.name}")
        new_embed.timestamp = discord.utils.utcnow()
        new_embed.set_thumbnail(url=ctx.author.avatar.url)
        with open(f'config/{ctx.guild.id}/config.json', 'r') as f:
            config = json.load(f)
        channel = self.bot.get_channel(config['channel_config']['rolepost_channel'])
        await channel.send(embed=new_embed)

def setup(bot):
    bot.add_cog(Voice(bot))
