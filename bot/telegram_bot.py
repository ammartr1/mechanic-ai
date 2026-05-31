import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
HF_API_URL = os.getenv("HF_API_URL", "https://ammartr1-mechanic-ai-api.hf.space")

def query_model(problem, model, year):
    try:
        url = f"{HF_API_URL}/api/predict"
        response = requests.post(url, json={
            "data": [problem, model, year, ""]
        }, timeout=120)
        if response.status_code == 200:
            result = response.json()
            return result.get('data', ['⚠️ لا يوجد رد'])[0]
        return f"⚠️ خطأ {response.status_code}: جاري إيقاظ النموذج... حاول بعد 30 ثانية"
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)[:200]}"

async def start(update: Update, context):
    await update.message.reply_text(
        "🔧 **ميكانيك-AI** في خدمتك!\n\n"
        "أرسل استفسارك بهذا التنسيق:\n"
        "`الموديل | السنة | المشكلة`\n\n"
        "مثال:\n"
        "`Toyota Camry | 2020 | صوت طقطقة في المحرك`\n\n"
        "أو أرسل المشكلة مباشرة.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context):
    text = update.message.text
    
    await update.message.chat.send_action("typing")
    
    try:
        parts = [p.strip() for p in text.split("|")]
        if len(parts) >= 3:
            model = parts[0]
            year = parts[1]
            problem = " | ".join(parts[2:])
        else:
            model = "غير محدد"
            year = "2020"
            problem = text
        
        response = query_model(problem, model, year)
        await update.message.reply_text(response[:4000])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطأ: {str(e)[:200]}")

def main():
    if not TELEGRAM_TOKEN:
        print("[!] خطأ: TELEGRAM_TOKEN غير موجود")
        return
    
    print(f"[*] HF_API_URL: {HF_API_URL}")
    print("[*] بدء تشغيل البوت...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("[✓] بوت ميكانيك-AI قيد التشغيل...")
    app.run_polling()

if __name__ == "__main__":
    main()
