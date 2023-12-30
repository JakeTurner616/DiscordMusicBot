import asyncio
import os
import re
import shutil
import subprocess
import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
from pytube import YouTube
from pydub import AudioSegment # for .mp3 conversion

intents = discord.Intents.default()
intents.message_content = True
# Set up the bot with a command prefix
bot = commands.Bot(command_prefix='!', intents=intents)

picard_path = r'/MusicBrainz-Picard-2.10.exe'  # Replace with the actual path

# Sanitize function to replace invalid characters
def sanitize_filename(filename):
    invalid_chars = r'<>:"/\|?*'
    return ''.join(c if c not in invalid_chars else '_' for c in filename)

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
                # Create the directory only if it does not exist
                if not os.path.exists("/Temp"):
                    try:
                        # Create the directory if it doesn't exist
                        os.makedirs("/Temp")
                        print(f"Directory '/Temp' created.")
                    except OSError as e:
                        # Handle the exception if the directory creation fails
                        print(f"Error: {e}")
                else:
                    print(f"Directory '/Temp' already exists.")


                yt = YouTube(selected_result)
                sanitized_title = sanitize_filename(yt.title)
                audio_path = f'Temp/{sanitized_title}'  # Let pytube handle the file extension
                yt.streams.first().download(output_path='Temp', filename=sanitized_title)
                print(f"Audio downloaded for user {user}: {yt.title}")

                # Wait for a short duration to ensure the file is fully downloaded
                await asyncio.sleep(5)  # You can adjust the duration based on your requirements

                # Convert to .mp3 using pydub
                mp3_filename = f"{sanitized_title}.mp3"
                mp3_path = os.path.abspath(os.path.join('Temp', mp3_filename))
                audio = AudioSegment.from_file(os.path.abspath(audio_path), format="mp4")
                audio.export(mp3_path, format="mp3")
                print(f"Audio converted to mp3 for user {user}: {yt.title}")

                # Remove the original downloaded file using the absolute path
                os.remove(os.path.abspath(audio_path))

                picard_executable = r"MusicBrainz-Picard-2.10.exe"

                def load_and_cluster(file_path):

                    # Load the file into MusicBrainz Picard
                    cluster = subprocess.run([picard_executable, file_path])

                def save():
                    subprocess.run([f"{picard_executable} -e SAVE_MATCHED; QUIT"])

                    
                folder_path = "Temp"
                extension = ".mp3"

                # Get a list of all files in the Temp folder
                files_in_folder = os.listdir(folder_path)

                # Filter the list to include only files with the specified extension
                mp3_files = [file for file in files_in_folder if file.endswith(extension)]

                # Check if there are any .mp3 files in the folder
                if mp3_files:
                    # If there are, choose the first one (you can modify this logic based on your requirements)
                    file_path = os.path.join(folder_path, mp3_files[0])
                    print("Found .mp3 file:", file_path)
                else:
                    print("No .mp3 files found in the Temp folder")

                # Load and cluster the file with MusicBrainz Picard
                load_and_cluster(file_path)
                save()

                shutil.rmtree("/Temp")


            

            except Exception as e:
                print(e)

# Run the bot with your token
bot.run('bot token goes here')
