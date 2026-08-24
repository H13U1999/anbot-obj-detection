import asyncio
import io
import os
import re

import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import emoji
from youtubesearchpython import VideosSearch
import requests

load_dotenv()

# discord.py 2.x requires intents to be declared. `message_content` is privileged:
# enable it in the Developer Portal, or prefix commands and the research mention
# both arrive with empty content and the bot looks silently dead.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = commands.Bot(command_prefix=os.environ.get('PREFIX', '!'), intents=intents)

headers_ = {
"Content-Type": "application/json"
}

# --- research -------------------------------------------------------------

ACK_MESSAGE = "Sure, let me do it for you."
USAGE = "Ask me like this:\n`@An bot research_for_me: your question here`"
DISCORD_MESSAGE_LIMIT = 2000

# Colon optional, case-insensitive, DOTALL so a question can span lines.
TRIGGER = re.compile(r"^research[_ ]?for[_ ]?me\s*:?\s*(.*)$", re.IGNORECASE | re.DOTALL)

# One research run per user at a time - a run is expensive and a mention is one
# keystroke.
_in_flight = set()


async def handle_research(message):
    """Return True if this message was a research request and was handled."""
    # Match the literal mention rather than `client.user.mentioned_in`: that helper
    # also fires on @everyone, and replying to one of the bot's own messages adds
    # the bot to `message.mentions` without the user having typed anything.
    mention = re.compile(r"<@!?%s>" % client.user.id)
    if not mention.search(message.content):
        return False

    match = TRIGGER.match(mention.sub("", message.content).strip())
    if not match:
        return False

    query = match.group(1).strip()
    if not query:
        await message.reply("What should I research?\n" + USAGE)
        return True

    if message.author.id in _in_flight:
        await message.reply("I'm still working on your last question - one at a time.")
        return True

    await message.reply(ACK_MESSAGE)
    _in_flight.add(message.author.id)
    # Detach: `on_message` must return quickly or it blocks the gateway heartbeat.
    asyncio.create_task(_run_research_task(message, query))
    return True


async def _run_research_task(message, query):
    try:
        async with message.channel.typing():
            report = await run_research(query)
    except Exception as e:
        print('research failed for %r: %s' % (query, e))
        await message.reply("Something went wrong while researching that. Try again?")
        return
    finally:
        _in_flight.discard(message.author.id)

    await send_report(message, report)


async def run_research(query):
    """Placeholder for the real research pipeline.

    Replace the body with a call into your agent / API. Keep it async - if the
    real implementation blocks, wrap it in `asyncio.to_thread(...)`.
    """
    await asyncio.sleep(3)  # stand-in for real work
    return "# Research: %s\n\n_Not implemented yet._" % query


async def send_report(message, report):
    """Post the report, falling back to a file past Discord's 2000-char limit."""
    if len(report) <= DISCORD_MESSAGE_LIMIT:
        await message.reply(report)
        return
    attachment = discord.File(io.BytesIO(report.encode("utf-8")), filename="research.md")
    await message.reply("Here's what I found:", file=attachment)


# --- ML services ----------------------------------------------------------

@client.command()
async def dect(ctx,  *message):
        if ctx.message.attachments:
            url = str(ctx.message.attachments[0])
            body ={"img": url}
            req = requests.post(os.environ.get('DECT_API'), json=body, headers=headers_)
            await ctx.send(req.json()["url"])
        else:
            await ctx.send("Please paste image")

@client.command()
async def nts(ctx,  *message):
        if ctx.message.attachments:
            if len(ctx.message.attachments) == 2:
                url_1 = str(ctx.message.attachments[1])
                url_2 = str(ctx.message.attachments[0])
                body ={"img_1": url_1, "img_2": url_2}
                req = requests.post(os.environ.get('NTS_API'), json=body, headers=headers_)
                await ctx.send(req.json()["url"])
            else:
                await ctx.send("Please send 2 images : 1. original image, 2. the image contain the style")
        else:
            await ctx.send("Please send 2 images : 1. original image, 2. the image contain the style")


# --- voice ----------------------------------------------------------------

@client.command()
async def join(ctx):
    isJoined = False
    voice = get(client.voice_clients, guild=ctx.guild)

    bot_voice = ctx.guild.voice_client
    author_voice = ctx.author.voice
    if bot_voice and bot_voice.is_connected():
        if bot_voice.channel != author_voice.channel:
            await voice.move_to(author_voice.channel)
        isJoined = True
    elif author_voice and not bot_voice:  # Author connected but bot not connected
        voice = await author_voice.channel.connect()
        isJoined = True
    elif not author_voice:  # Author not connected
        await ctx.send("Get in a voice channel")

    return isJoined


@client.command()
async def play(ctx, *url):
    if not await join(ctx):
        return

    YDL_OPTIONS = {'format': 'bestaudio',
                   'extractaudio': True,
                   'noplaylist': True,
                   }
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    voice = get(client.voice_clients, guild=ctx.guild)

    searchKey = ' '.join(url)
    if not voice.is_playing():
        result = ytVideoSearchLink(searchKey)
        if result is None:
            await ctx.send('Bot cannot find ' + searchKey)
            return
        link = result.get("link")
        title = result.get("title")
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(
                link, download=False)
        URL = info['url']
        voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        await ctx.send('Bot is playing ' + title + '\n' + link)


# check if the bot is already playing
    else:
        await ctx.send("Bot is playing")
        return


@client.command()
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if not voice.is_playing():
        voice.resume()
        await ctx.send("resuming")


@client.command()
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send("paused")


@client.command()
async def skip(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send("skipping")


@client.command()
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.send("stopping")


@client.command()
async def leave(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()


@client.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)
    await ctx.send("Messages have been cleared")


@client.command()
async def search(ctx, *search):
    print(ytVideoSearchLink(search))


# --- events ---------------------------------------------------------------

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # Ignore the bot's own messages first - the original processed commands
    # before this check.
    if message.author.bot:
        return

    if await handle_research(message):
        return

    await client.process_commands(message)

    if message.content.startswith('hello'):
        await message.channel.send('kkk')
    if message.content.startswith("play"):
        await message.channel.send("What do you want to play?")


@client.event
async def on_reaction_add(reaction, user):
    channelId = reaction.message.channel.id
    Channel = client.get_channel(channelId)
    reaction_emoji = emoji.demojize(reaction.emoji)
    print(reaction_emoji)
    if reaction.message.channel != Channel:
        return
    if (user.id == client.user.id):
        return
    if reaction.emoji == '\U0001F3C0':
        await Channel.send("sup bitch")


def ytVideoSearchLink(search, limit=1):
    videoSearch = VideosSearch(search, limit=1)
    list = dict(enumerate(videoSearch.result().get("result"))).get(limit-1)
    print(list)
    return list


token = os.environ.get('TOKEN')
if not token:
    raise SystemExit("TOKEN is empty - set it in the repo-root .env that docker-compose reads")
client.run(token)
