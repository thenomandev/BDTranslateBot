import os
import logging

from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from googletrans import Translator


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# =========================
# Bot Token
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable সেট করা নেই!"
    )


# =========================
# Flask + Telegram Bot
# =========================

bot = Bot(token=TOKEN)

app = Flask(__name__)


# =========================
# Google Translator
# =========================

translator = Translator(
    service_urls=[
        "translate.googleapis.com"
    ]
)


# =========================
# Telegram Dispatcher
# =========================

dispatcher = Dispatcher(
    bot,
    None,
    use_context=True
)


# =========================
# Translation Function
# =========================

def translate_text(text):
    """
    Automatically detects the language.

    English -> Bangla
    Bangla  -> English
    Other   -> Bangla
    """

    if not text or not text.strip():
        return None

    text = text.strip()

    try:

        # Detect language
        detected = translator.detect(text)

        lang = detected.lang.lower()

        logger.info(
            "Detected language: %s | Text: %s",
            lang,
            text[:100]
        )


        # English -> Bangla
        if lang == "en":

            destination = "bn"


        # Bangla -> English
        elif lang == "bn":

            destination = "en"


        # Other languages -> Bangla
        else:

            destination = "bn"


        # Translate
        result = translator.translate(
            text,
            dest=destination
        )

        translated_text = result.text

        logger.info(
            "Translation successful: %s",
            translated_text[:100]
        )

        return translated_text


    except Exception as e:

        logger.exception(
            "Translation error: %s",
            e
        )

        return None


# =========================
# Normal Message Handler
# =========================

def handle_message(update, context):

    try:

        # Make sure message exists
        if not update.message:
            return

        # Make sure text exists
        if not update.message.text:
            return

        text = update.message.text.strip()

        if not text:
            return


        # Translate
        translated = translate_text(text)


        # Success
        if translated:

            update.message.reply_text(
                f"🔁 {translated}"
            )


        # Failed
        else:

            update.message.reply_text(
                "❌ অনুবাদ করা যায়নি।\n"
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
            )


    except Exception as e:

        logger.exception(
            "Message handler error: %s",
            e
        )


# =========================
# /translate Command
# =========================

def translate_command(update, context):

    try:

        # No text after /translate
        if not context.args:

            update.message.reply_text(
                "⚠️ দয়া করে /translate এর পরে কিছু লিখুন।\n\n"
                "উদাহরণ:\n"
                "/translate Hello"
            )

            return


        # Join command arguments
        text = " ".join(context.args).strip()


        # Translate
        translated = translate_text(text)


        # Success
        if translated:

            update.message.reply_text(
                f"🔁 {translated}"
            )


        # Failed
        else:

            update.message.reply_text(
                "❌ অনুবাদ করা যায়নি।\n"
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
            )


    except Exception as e:

        logger.exception(
            "Command translation error: %s",
            e
        )


# =========================
# Telegram Handlers
# =========================

dispatcher.add_handler(
    MessageHandler(
        Filters.text & ~Filters.command,
        handle_message
    )
)

dispatcher.add_handler(
    CommandHandler(
        "translate",
        translate_command
    )
)


# =========================
# Webhook
# =========================

@app.route(
    f"/{TOKEN}",
    methods=["POST"]
)
def webhook():

    try:

        data = request.get_json(
            force=True
        )

        if not data:
            return "No data", 400


        update = Update.de_json(
            data,
            bot
        )


        dispatcher.process_update(
            update
        )


        return "OK", 200


    except Exception as e:

        logger.exception(
            "Webhook error: %s",
            e
        )

        return "ERROR", 500


# =========================
# Home / Status
# =========================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return (
        "BD Translate Bot is live!",
        200
    )


# =========================
# Start Flask Server
# =========================

if __name__ == "__main__":

    PORT = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    logger.info(
        "Starting Flask server on port %s...",
        PORT
    )


    app.run(
        host="0.0.0.0",
        port=PORT
    )
