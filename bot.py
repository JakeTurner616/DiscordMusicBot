import asyncio
import os
import re
import subprocess
import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
from pytube import YouTube
from pydub import AudioSegment # for .mp3 conversion
import configparser  # Import the configparser module

config = configparser.ConfigParser()
config.read('config.ini')
bot_prefix = config.get('Bot', 'Prefix')

intents = discord.Intents.default()
intents.message_content = True
# Set up the bot with a command prefix
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)


# Sanitize function to replace invalid characters
def sanitize_filename(filename):
    invalid_chars = r'<>:"/\|?*'
    return ''.join(c if c not in invalid_chars else '_' for c in filename)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print("-------")


# Command to search for YouTube videos
@bot.command(name='search')
async def search(ctx, *, query):
    results = YoutubeSearch(query, max_results=5).to_dict()

    embed = discord.Embed(title="YouTube Search Results", color=discord.Color.blue())

    # Add the first 5 search results to the embed
    for i, result in enumerate(results):
        title = result['title']
        link = f"https://www.youtube.com/watch?v={result['id']}"
        embed.add_field(name=f"{i+1}. {title}", value=link, inline=False)

    message = await ctx.send(embed=embed)

    # Add reactions to the message for user selection
    for i in range(1, 6):
        await message.add_reaction(f"{i}\U0000FE0F\U000020E3")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or not isinstance(reaction.emoji, str):
        return
    expected_emojis = [f"{i}\U0000FE0F\U000020E3" for i in range(1, 6)]
    print(f"{user} reacted with {reaction.emoji}")

    if reaction.emoji not in expected_emojis:
        return

    try:
        # Show typing indicator
        async with reaction.message.channel.typing():
            processing_embed = discord.Embed(
                title=f"Downloading video #{reaction.emoji} added by {user}.",
                description=f"Youtube video is now downloading.",
                color=discord.Color.blue()
            )
            processing_message = await reaction.message.channel.send(embed=processing_embed)

            # Delete the search results embed
            await reaction.message.delete()

            match = re.match(r'^(\d+)\U0000FE0F\U000020E3$', reaction.emoji)
            if match:
                result_index = int(match.group(1)) - 1
                message = reaction.message

                if message.embeds and message.embeds[0].title == "YouTube Search Results":
                    try:
                        selected_result = message.embeds[0].fields[result_index].value
                        yt = YouTube(selected_result)
                        await asyncio.sleep(2) # Given a short video, the download is nearly instantaneous. Therefore, we can use a short time delay; otherwise, this embed is essentially pointless as it switches too quickly to read.
                        # Update the embed to indicate downloading progress
                        processing_embed.title = "Converting audio to mp3..."
                        processing_embed.description = f"Downloading {yt.title} added by {user}."
                        await processing_message.edit(embed=processing_embed)

                        audio_stream = yt.streams.filter(only_audio=True).first()
                        sanitized_title = sanitize_filename(yt.title)
                        audio_path = os.path.join('Temp', sanitized_title)
                        audio_stream.download(output_path='Temp', filename=sanitized_title)
                        print(f"Audio downloaded for user {user}: {yt.title}")

                        audio = AudioSegment.from_file(audio_path, format="mp4")
                        mp3_path = f'Temp/{sanitized_title}.mp3'
                        audio.export(mp3_path, format="mp3")
                        print(f"Audio converted to mp3 for user {user}: {yt.title}")

                        os.remove(audio_path)

                        picard_raw_path = config.get('Bot', 'picard_path')
                        picard_path = picard_raw_path

                        # Update the embed to indicate it is being sent to picard
                        processing_embed.title = "Conversion complete. Sending to picard..."
                        processing_embed.description = f"Sending {yt.title} to picard added by {user}."
                        await processing_message.edit(embed=processing_embed)

                        command = [picard_path, "-e", "LOAD", mp3_path, "-e", "SAVE_MATCHED", "-e", "QUIT"]
                        subprocess.run(command)
                        await asyncio.sleep(2)

                        # Update the embed to indicate completion
                        processing_embed.title = f"Download completed for {yt.title}"
                        processing_embed.description = "The audio has been successfully downloaded and processed."
                        processing_embed.color = discord.Color.green()
                        await processing_message.edit(embed=processing_embed)

                    except Exception as e:
                        print(f"Error downloading, converting, and processing audio for user {user}: {str(e)}")
                        # Update the embed to indicate an error
                        processing_embed.title = "Error processing your request"
                        processing_embed.description = f"An error occurred: {str(e)}"
                        processing_embed.color = discord.Color.red()
                        await processing_message.edit(embed=processing_embed)

                    finally:
                        # After successful processing or in case of an error, clear unnecessary fields
                        processing_embed.clear_fields()
                        await processing_message.edit(embed=processing_embed)
    finally:
        # Clear reactions including the typing indicator
        await processing_message.clear_reactions()

# Run the bot with your token
bot_token = config.get('Bot', 'Token')

bot.run(bot_token)
