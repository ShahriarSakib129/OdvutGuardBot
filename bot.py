import os
import re
import logging
import threading

from flask import Flask
from telegram import Update, MessageEntity
from telegram.ext import Application, MessageHandler, ContextTypes, filters


# =========================
# Logging
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================
# Bot Token
# =========================

TOKEN = os.getenv("BOT_TOKEN")


# =========================
# Flask Health Server
# =========================

web = Flask(__name__)


@web.route("/")
def home():
    return "🛡️ Odvut Guard Bot is running!"


@web.route("/health")
def health():
    return "OK", 200


def run_web_server():
    port = int(os.getenv("PORT", 10000))

    web.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# Link Detection
# =========================

LINK_PATTERN = re.compile(
    r"("
    r"https?://[^\s]+|"
    r"www\.[^\s]+|"
    r"t\.me/[^\s]+|"
    r"[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?"
    r")",
    re.IGNORECASE
)


# =========================
# Admin Check
# =========================

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


# =========================
# Delete Link
# =========================

async def delete_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message:
        return

    # Ignore messages from admins
    if await is_admin(update, context):
        return

    text = message.text or message.caption or ""

    has_link = False

    # Telegram detected links
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

    # Normal text link detection
    if LINK_PATTERN.search(text):

        has_link = True

    # Delete message
    if has_link:

        try:

            await message.delete()

            user = update.effective_user

            logger.info(
                f"Link deleted from "
                f"{user.full_name} "
                f"(ID: {user.id})"
            )

        except Exception as e:

            logger.error(
                f"Delete error: {e}"
            )


# =========================
# Main
# =========================

def main():

    if not TOKEN:

        logger.error(
            "BOT_TOKEN environment variable not found!"
        )

        return

    # Start health server
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Telegram bot
    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Check all messages
    app.add_handler(
        MessageHandler(
            filters.ALL,
            delete_link
        )
    )

    print("🛡️ Odvut Guard Bot is running...")
    print("❤️ Health server is running...")

    # IMPORTANT:
    # Do NOT use drop_pending_updates=True
    app.run_polling()


if __name__ == "__main__":
    main()
