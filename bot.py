import os
import re
import logging

from telegram import Update, MessageEntity
from telegram.ext import Application, MessageHandler, ContextTypes, filters


# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# Get bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")


# Link detection pattern
LINK_PATTERN = re.compile(
    r"("
    r"https?://[^\s]+|"       # http:// or https://
    r"www\.[^\s]+|"          # www.example.com
    r"t\.me/[^\s]+|"         # Telegram links
    r"[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?"  # example.com
    r")",
    re.IGNORECASE
)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )

        return member.status in [
            "creator",
            "administrator"
        ]

    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return False


async def delete_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message:
        return

    # Don't delete messages from admins
    if await is_admin(update, context):
        return

    text = message.text or message.caption or ""

    has_link = False


    # Check Telegram link entities
    entities = []

    if message.entities:
        entities.extend(message.entities)

    if message.caption_entities:
        entities.extend(message.caption_entities)

    for entity in entities:

        if entity.type in [
            MessageEntity.URL,
            MessageEntity.TEXT_LINK
        ]:

            has_link = True
            break


    # Check normal text links
    if LINK_PATTERN.search(text):
        has_link = True


    # Delete message if link found
    if has_link:

        try:

            await message.delete()

            user = update.effective_user

            logger.info(
                f"Link deleted from {user.full_name} "
                f"(ID: {user.id})"
            )

        except Exception as e:

            logger.error(
                f"Delete error: {e}"
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🛡️ Odvut Guard Bot is active!"
    )


def main():

    if not TOKEN:

        logger.error(
            "BOT_TOKEN environment variable not found!"
        )

        return


    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )


    # Link detection
    app.add_handler(
        MessageHandler(
            filters.ALL,
            delete_link
        )
    )


    print("🛡️ Odvut Guard Bot is running...")


    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()