# bot.py
import asyncio
import time
import logging
import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from retrieval import generate_answer

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("GuideBot")

# ----- Intents -----
intents = discord.Intents.default()
intents.message_content = True  # must be enabled in Dev Portal too

# ----- Bot -----
bot = commands.Bot(command_prefix=None, intents=intents)  # no prefix; responds to raw messages or mentions

# Simple per-user rate limit (seconds between queries)
USER_COOLDOWN = 2.0
_last_seen = {}  # user_id -> timestamp


@bot.event
async def on_ready():
    log.info(f"Bot logged in as {bot.user} (id={bot.user.id})")


def is_trigger_message(message: discord.Message) -> bool:
    """
    Decide whether to respond:
    - If bot is mentioned explicitly OR
    - If message is a direct DM OR
    - If message is plain text not beginning with common command prefixes
    """
    if message.author.bot:
        return False

    # DM always reply
    if isinstance(message.channel, discord.DMChannel):
        return True

    # Mention triggers
    if bot.user.mentioned_in(message):
        return True

    # Simple chat: respond to plain statements (not starting with / or ! or .)
    txt = message.content.strip()
    if not txt:
        return False
    if txt.startswith(("/", "!", ".")):
        return False

    # optionally: restrict to certain channel ids by adding checks here

    return True


@bot.event
async def on_message(message: discord.Message):
    if not is_trigger_message(message):
        # still allow commands to process
        await bot.process_commands(message)
        return

    # Simple cooldown per user
    now = time.time()
    last = _last_seen.get(message.author.id, 0)
    if now - last < USER_COOLDOWN:
        # politely ignore or optionally send a small notice
        try:
            await message.add_reaction("⏳")
        except Exception:
            pass
        return
    _last_seen[message.author.id] = now

    # Normalize query (remove mention text)
    content = message.content.replace(f"<@!{bot.user.id}>", "").replace(f"<@{bot.user.id}>", "").strip()

    # Show typing indicator while processing
    try:
        async with message.channel.typing():
            # Use asyncio.wait_for to cap the whole retrieval+generation time
            try:
                answer = await asyncio.wait_for(generate_answer(content), timeout=60.0)
            except asyncio.TimeoutError:
                answer = "Sorry — the model is taking too long. Try again in a bit."
            except Exception as e:
                log.exception("generate_answer failed")
                answer = f"Error while generating answer: {e}"

    except Exception as e:
        # If typing context fails, fallback to direct call (still async)
        log.exception("Typing context failed")
        try:
            answer = await generate_answer(content)
        except Exception as e2:
            answer = f"Error while generating answer: {e2}"

    # Respond (as reply to keep thread)
    try:
        # short-circuit empty answer
        if not answer:
            answer = "I couldn't find an answer in the dataset."
        await message.reply(answer, mention_author=False)
    except Exception:
        log.exception("Failed to send message response")

    # allow commands processing too
    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
