import os
import io
import logging
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===================== CONFIGURATION =====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8697465308:AAEtqBKPgr1oWq0VSnmbVO_DCXRXjE1pK-Y")
HF_API_TOKEN = os.environ.get("HF_TOKEN", "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")
HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
PORT = int(os.environ.get("PORT", 8080))
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Flask app (sirf ping ke liye) ──────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is alive and running!", 200

@flask_app.route("/ping")
def ping():
    return "pong", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)
# ───────────────────────────────────────────────────────


def generate_image(prompt: str):
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
    }
    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 503:
            return "loading"
        else:
            logger.error(f"HF Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Request error: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"🎨 Namaste {user}! Main Text-to-Image Bot hoon!\n\n"
        "📝 Kaise use karo:\n"
        "Bas koi bhi image description likhо, main generate kar dunga!\n\n"
        "📌 Examples:\n"
        "• a beautiful sunset over mountains\n"
        "• cute cat sitting on a couch\n"
        "• futuristic city at night, neon lights\n\n"
        "⚡ Commands:\n"
        "/start - Bot start karo\n"
        "/help - Help dekho\n"
        "/examples - Examples dekho\n\n"
        "✍️ Abhi koi description likhо!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 Help Guide\n\n"
        "1️⃣ Koi bhi text likhо (English mein)\n"
        "2️⃣ Bot 20-40 seconds mein image banayega\n"
        "3️⃣ Image download kar lo!\n\n"
        "💡 Tips for better images:\n"
        "• Detailed description likhо\n"
        "• Style mention karo: realistic, cartoon, anime, oil painting\n"
        "• Lighting mention karo: sunset, night, bright\n\n"
        "Example: realistic photo of a lion in jungle, golden hour lighting"
    )


async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Example Prompts:\n\n"
        "🌅 a beautiful sunset over snow mountains, realistic\n\n"
        "🐱 cute anime cat with blue eyes, digital art\n\n"
        "🏙️ futuristic cyberpunk city at night, neon lights, rain\n\n"
        "🌸 cherry blossom garden in Japan, spring, watercolor painting\n\n"
        "👨‍🚀 astronaut floating in space, earth in background, realistic\n\n"
        "Inhe copy karke bhejo ya apna khud likhо! 😊"
    )


async def generate_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()

    if len(prompt) < 3:
        await update.message.reply_text("❌ Thoda bada description likhо please!")
        return

    processing_msg = await update.message.reply_text(
        f"🎨 Image generate ho rahi hai...\n"
        f"⏳ 20-40 seconds wait karo!\n"
        f"📝 Prompt: {prompt[:100]}"
    )

    result = generate_image(prompt)

    if result == "loading":
        await processing_msg.edit_text(
            "⏳ Model load ho raha hai (pehli baar thoda time lagta hai)...\n"
            "🔄 60 seconds baad dobara try karo!"
        )
        return

    if result is None:
        await processing_msg.edit_text(
            "❌ Image generate nahi hui. Dobara try karo!\n"
            "💡 Tip: English mein likhо aur detail dо"
        )
        return

    image_bytes = io.BytesIO(result)
    image_bytes.name = "generated_image.png"

    await processing_msg.delete()
    await update.message.reply_photo(
        photo=image_bytes,
        caption=f"✅ Image Ready!\n📝 {prompt[:200]}\n\n🔄 Naya image ke liye naya text likhо!"
    )


def main():
    print("🌐 Flask server shuru ho raha hai (ping ke liye)...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("🤖 Telegram Bot shuru ho raha hai...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("examples", examples_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image_handler))
    print("✅ Bot chal raha hai! 24/7 online.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
