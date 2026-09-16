import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from googletrans import Translator

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable সেট করা নেই!")

# Flask + Telegram Bot
bot = Bot(token=TOKEN)
app = Flask(__name__)

# Use Google's direct translation endpoint
translator = Translator(
    service_urls=["translate.googleapis.com"]
)

# Dispatcher
dispatcher = Dispatcher(bot, None, use_context=True)


def translate_text(text):
    """
    English <-> Bangla translation
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
            dest_lang = "bn"

        # Bangla -> English
        elif lang == "bn":
            dest_lang = "en"

        # Other languages -> Bangla
        else:
            dest_lang = "bn"

        result = translator.translate(
            text,
            dest=dest_lang
        )

        return result.text

    except Exception as e:
        logger.exception("Translation error")
        return None


# Normal message handler
def handle_message(update, context):

    if not update.message or not update.message.text:
        return

    text = update.message.text

    translated = translate_text(text)

    if translated:
        update.message.reply_text(f"🔁 {translated}")
    else:
        update.message.reply_text(
            "❌ অনুবাদ করা যায়নি। একটু পরে আবার চেষ্টা করুন।"
        )


# /translate command
def translate_command(update, context):

    if not context.args:
        update.message.reply_text(
            "⚠️ দয়া করে /translate এর পরে কিছু লিখুন।\n\n"
            "উদাহরণ:\n"
            "/translate Hello"
        )
        return

    text = " ".join(context.args)

    translated = translate_text(text)

    if translated:
        update.message.reply_text(
            f"🔁 {translated}"
        )
    else:
        update.message.reply_text(
            "❌ অনুবাদ করা যায়নি। একটু পরে আবার চেষ্টা করুন।"
        )


# Handlers
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


# Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():

    try:
        data = request.get_json(force=True)

        update = Update.de_json(
            data,
            bot
        )

        dispatcher.process_update(update)

        return "OK", 200

    except Exception as e:

        logger.exception(
            "Webhook error"
        )

        return "ERROR", 500


# Status
@app.route("/", methods=["GET"])
def index():
    return "BD Translate Bot is live!", 200


# Start Flask
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
