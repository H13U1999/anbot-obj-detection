"""Research bot - initial template.

Trigger: mention the bot in any channel it can read.

    @research_for_me what are the tradeoffs between Postgres and SQLite?

It acknowledges immediately, then runs the research in the background so the
gateway connection stays responsive.

Required env vars (see .env.example):
    TOKEN   Discord bot token

The `message_content` privileged intent must be enabled for this bot in the
Discord Developer Portal, otherwise `message.content` arrives empty and the
mention is never seen.
"""

import asyncio
import io
import logging
import os
import re

import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("research-bot")

ACK_MESSAGE = "Sure, let me do it for you."
DISCORD_MESSAGE_LIMIT = 2000

intents = discord.Intents.default()
intents.message_content = True  # privileged - enable it in the Developer Portal

client = discord.Client(intents=intents)

# One research run per user at a time. A run is expensive and a mention is one
# keystroke, so without this a user can trivially fan out a dozen of them.
_in_flight: set[int] = set()


@client.event
async def on_ready():
    log.info("logged in as %s (id=%s)", client.user, client.user.id)


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Match the literal mention in the text rather than `client.user.mentioned_in`:
    # that helper also fires on @everyone, and replying to one of the bot's own
    # messages silently adds the bot to `message.mentions` without the user
    # having typed anything.
    mention = re.compile(rf"<@!?{client.user.id}>")
    if not mention.search(message.content):
        return

    query = mention.sub("", message.content).strip()
    if not query:
        await message.reply("Mention me with a question and I'll research it.")
        return

    if message.author.id in _in_flight:
        await message.reply("I'm still working on your last question - one at a time.")
        return

    await message.reply(ACK_MESSAGE)

    _in_flight.add(message.author.id)
    # Detach: `on_message` must return quickly or it blocks the gateway heartbeat.
    asyncio.create_task(_handle(message, query))


async def _handle(message: discord.Message, query: str):
    """Run the research and post the result back to the originating channel."""
    log.info("research requested by %s: %r", message.author, query)
    try:
        async with message.channel.typing():
            report = await run_research(query)
    except Exception:
        log.exception("research failed for %r", query)
        await message.reply("Something went wrong while researching that. Try again?")
        return
    finally:
        _in_flight.discard(message.author.id)

    await send_report(message, report)


async def run_research(query: str) -> str:
    """Placeholder for the actual research pipeline.

    Replace the body with a call into your agent / API. Keep it `async` and keep
    it off the event loop's back - if the real implementation is blocking, wrap
    it in `asyncio.to_thread(...)`.
    """
    await asyncio.sleep(3)  # stand-in for real work
    return f"# Research: {query}\n\n_Not implemented yet._"


async def send_report(message: discord.Message, report: str):
    """Post `report`, falling back to a file attachment past Discord's limit.

    Discord rejects a message body over 2000 characters outright rather than
    truncating, and a research report will exceed that most of the time.
    """
    if len(report) <= DISCORD_MESSAGE_LIMIT:
        await message.reply(report)
        return

    attachment = discord.File(io.BytesIO(report.encode("utf-8")), filename="research.md")
    await message.reply("Here's what I found:", file=attachment)


def main():
    token = os.environ.get("TOKEN")
    if not token:
        raise SystemExit("TOKEN is not set - copy .env.example to .env and fill it in")
    client.run(token)


if __name__ == "__main__":
    main()
