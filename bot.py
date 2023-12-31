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

# Event listener for reaction added
@bot.event
async def on_reaction_add(reaction, user):
    # Check if the reaction is from the bot or a DM
    if user.bot or not isinstance(reaction.emoji, str):
        return

    # Use regular expression to extract numeric part of the emoji
    match = re.match(r'^(\d+)\U0000FE0F\U000020E3$', reaction.emoji)
    if match:
        result_index = int(match.group(1)) - 1

        # Get the message that contains the search results
        message = reaction.message

        # Check if the message is the search result message
        if message.embeds and message.embeds[0].title == "YouTube Search Results":
            # Get the link of the selected result
            selected_result = message.embeds[0].fields[result_index].value

            # Download audio using pytube
            try:
                yt = YouTube(selected_result)
                audio_stream = yt.streams.filter(only_audio=True).first()
                sanitized_title = sanitize_filename(yt.title)
                audio_path = os.path.join('Temp', sanitized_title)
                audio_stream.download(output_path='Temp', filename=sanitized_title)
                print(f"Audio downloaded for user {user}: {yt.title}")

                # Convert to .mp3 using pydub from null extension
                audio = AudioSegment.from_file(audio_path, format="mp4")
                mp3_path = f'Temp/{sanitized_title}.mp3'
                audio.export(mp3_path, format="mp3")
                print(f"Audio converted to mp3 for user {user}: {yt.title}")

                # Remove the original null extension file
                os.remove(audio_path)

                print(f"mp3 path: {mp3_path}")

                # Set the path to the system specific MusicBrainz binary
                picard_raw_path = config.get('Bot', 'Picard_path')
                picard_path = picard_raw_path

                # Construct the command as a list of arguments
                command = [picard_path, "-e", "LOAD", mp3_path, "-e", "SAVE_MATCHED", "-e", "QUIT"]

                # Use subprocess.run to execute the command
                subprocess.run(command)
                await asyncio.sleep(2)  # Adjust the sleep duration as needed

            except Exception as e:
                print(f"Error downloading, converting, and processing audio for user {user}: {str(e)}")

# Run the bot with your token
bot_token = config.get('Bot', 'Token')

bot.run(bot_token)
