import os
import logging
import json
import urllib.parse
import urllib.request

from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters


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
    raise RuntimeError("BOT_TOKEN environment variable সেট করা নেই!")


# =========================
# Render URL
# =========================

RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not RENDER_URL:
    logger.warning(
        "RENDER_EXTERNAL_URL পাওয়া যায়নি। "
        "Webhook automatic সেট করা যাবে না।"
    )


# =========================
# Flask + Telegram Bot
# =========================

bot = Bot(token=TOKEN)

app = Flask(__name__)


# =========================
# Dispatcher
# =========================

dispatcher = Dispatcher(
    bot,
    None,
    use_context=True
)


# =========================
# Translation
# =========================

def translate_text(text):

    if not text or not text.strip():
        return None

    text = text.strip()

    try:

        # Detect language
        detect_url = (
            "https://translate.googleapis.com/"
            "translate_a/single?"
            + urllib.parse.urlencode({
                "client": "gtx",
                "sl": "auto",
                "tl": "en",
                "dt": "t",
                "q": text
            })
        )

        req = urllib.request.Request(
            detect_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=15
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )


        detected_lang = None

        if len(data) > 2:
            detected_lang = data[2]

        if detected_lang:
            detected_lang = detected_lang.lower()

        logger.info(
            "Detected language: %s",
            detected_lang
        )


        # Bangla -> English
        if detected_lang == "bn":
            destination = "en"

        # Everything else -> Bangla
        else:
            destination = "bn"


        # Translate
        translate_url = (
            "https://translate.googleapis.com/"
            "translate_a/single?"
            + urllib.parse.urlencode({
                "client": "gtx",
                "sl": "auto",
                "tl": destination,
                "dt": "t",
                "q": text
            })
        )

        req = urllib.request.Request(
            translate_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=15
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )


        translated_parts = []

        if data and data[0]:

            for item in data[0]:

                if item and item[0]:
                    translated_parts.append(item[0])


        translated = "".join(
            translated_parts
        ).strip()


        if not translated:
            logger.error("Empty translation response")
            return None


        logger.info(
            "Translation successful: %s",
            translated[:100]
        )

        return translated


    except Exception as e:

        logger.exception(
            "Translation error: %s",
            e
        )

        return None


# =========================
# Message Handler
# =========================

def handle_message(update, context):

    try:

        if not update.message:
            return

        if not update.message.text:
            return

        text = update.message.text.strip()

        if not text:
            return


        logger.info(
            "Received message: %s",
            text[:100]
        )


        translated = translate_text(text)


        if translated:

            update.message.reply_text(
                f"🔁 {translated}"
            )

        else:

            update.message.reply_text(
                "❌ অনুবাদ ব্যর্থ হয়েছে।\n"
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
            )


    except Exception:

        logger.exception(
            "Message handler error"
        )


# =========================
# /translate Command
# =========================

def translate_command(update, context):

    try:

        if not context.args:

            update.message.reply_text(
                "⚠️ দয়া করে /translate এর পরে "
                "কিছু লিখুন।\n\n"
                "উদাহরণ:\n"
                "/translate Hello"
            )

            return


        text = " ".join(
            context.args
        ).strip()


        logger.info(
            "Translate command: %s",
            text[:100]
        )


        translated = translate_text(text)


        if translated:

            update.message.reply_text(
                f"🔁 {translated}"
            )

        else:

            update.message.reply_text(
                "❌ অনুবাদ ব্যর্থ হয়েছে।\n"
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
            )


    except Exception:

        logger.exception(
            "Command translation error"
        )


# =========================
# Handlers
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
# Webhook Endpoint
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


        logger.info(
            "Telegram webhook request received"
        )


        update = Update.de_json(
            data,
            bot
        )


        dispatcher.process_update(
            update
        )


        return "OK", 200


    except Exception:

        logger.exception(
            "Webhook error"
        )

        return "ERROR", 500


# =========================
# Status
# =========================

@app.route("/")
def index():

    return "BD Translate Bot is live!", 200


# =========================
# Set Webhook
# =========================

def setup_webhook():

    try:

        if not RENDER_URL:

            logger.error(
                "RENDER_EXTERNAL_URL পাওয়া যায়নি!"
            )

            return


        webhook_url = (
            RENDER_URL.rstrip("/")
            + "/"
            + TOKEN
        )


        logger.info(
            "Setting Telegram webhook: %s",
            RENDER_URL.rstrip("/") + "/<TOKEN>"
        )


        result = bot.set_webhook(
            url=webhook_url
        )


        logger.info(
            "Webhook setup result: %s",
            result
        )


        info = bot.get_webhook_info()


        logger.info(
            "Webhook URL configured: %s",
            info.url
        )


        logger.info(
            "Pending updates: %s",
            info.pending_update_count
        )


    except Exception:

        logger.exception(
            "Failed to setup Telegram webhook"
        )


# =========================
# Start Server
# =========================

if __name__ == "__main__":

    PORT = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    # Set webhook before starting Flask
    setup_webhook()


    logger.info(
        "Starting Flask server on port %s...",
        PORT
    )


    app.run(
        host="0.0.0.0",
        port=PORT
        )
