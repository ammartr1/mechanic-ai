#!/usr/bin/env python3
"""بوت تيليجرام - ميكانيك-AI - خبير المركبات المطلق"""

import asyncio
import logging
import os
import json
import tempfile
from pathlib import Path
from io import BytesIO
from datetime import datetime

import torch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import whisper
from TTS.api import TTS
import requests
from googlesearch import search

# إعدادات
TELEGRAM_TOKEN = "8660571036:AAFCHE1EcV1-Tt5qjWvSsBCgzFdcZqTisWs"  # ضع توكن البوت هنا
MODEL_PATH = "../models/gguf/mechanic-ai-Q4_K_M.gguf"
DATABASE_PATH = "../data/chat_logs.db"

# تحميل النماذج
print("[*] تحميل النموذج...")
from llama_cpp import Llama
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_threads=8,
    n_gpu_layers=0,
    verbose=False
)

print("[*] تحميل Whisper...")
whisper_model = whisper.load_model("small")

print("[*] تحميل TTS...")
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

# === وظائف المساعدة ===

SYSTEM_PROMPT = """أنت ميكانيك-AI، الخبير العالمي المطلق في جميع أنواع المركبات والشاحنات والآليات.
أنت تفهم كل نظام في أي مركبة: ميكانيكي، كهربائي، هيدروليكي، نيوماتيكي، إلكتروني.
أنت تعرف كل الموديلات، كل الأعطال، وكل الحلول.
أجب بدقة كاملة، ثقة مطلقة، وخطوات تنفيذية مباشرة.
لا تقل "قد يكون" أو "ربما". قل "المشكلة هي" و"افعل هذا".
أجب بالعربية."""

def deep_search_google(query, num_results=5):
    """بحث عميق في جوجل"""
    results = []
    try:
        for url in search(query, num_results=num_results, lang="en"):
            results.append(url)
    except Exception as e:
        print(f"[-] خطأ بحث: {e}")
    return results

def query_model(prompt, images_context=""):
    """استعلام النموذج"""
    full_prompt = f"""{SYSTEM_PROMPT}

{images_context}

المستخدم: {prompt}
الميكانيك-AI:"""
    
    response = llm(
        full_prompt,
        max_tokens=1024,
        temperature=0.3,
        top_p=0.9,
        stop=["المستخدم:", "<|eot_id|>"],
        echo=False
    )
    
    return response['choices'][0]['text'].strip()

def analyze_image(image_path):
    """تحليل صورة باستخدام نموذج رؤية"""
    # استخدام Llama 3.2 Vision (إذا متوفر) أو LLaVA
    try:
        from transformers import LlavaForConditionalGeneration, AutoProcessor
        processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
        model = LlavaForConditionalGeneration.from_pretrained(
            "llava-hf/llava-1.5-7b-hf",
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        image = Image.open(image_path)
        inputs = processor("وصف ما تراه في هذه الصورة من أجزاء المركبة بالتفصيل:", image, return_tensors="pt")
        output = model.generate(**inputs, max_new_tokens=200)
        description = processor.decode(output[0], skip_special_tokens=True)
        return description
    except:
        return "[صورة مركبة مرفقة]"

def save_conversation(user_id, message, response):
    """حفظ المحادثة للتعلم الذاتي"""
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  timestamp TEXT,
                  message TEXT,
                  response TEXT)''')
    
    cursor.execute("INSERT INTO conversations VALUES (NULL, ?, ?, ?, ?)",
                  (str(user_id), datetime.now().isoformat(), message, response))
    conn.commit()
    conn.close()

# === معالجات البوت ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    keyboard = [
        [InlineKeyboardButton("🚗 تشخيص عطل", callback_data="diagnose")],
        [InlineKeyboardButton("🔧 صيانة دورية", callback_data="maintenance")],
        [InlineKeyboardButton("⚡ كهرباء", callback_data="electrical")],
        [InlineKeyboardButton("📸 إرسال صورة عطل", callback_data="photo")],
        [InlineKeyboardButton("🎤 إرسال رسالة صوتية", callback_data="voice")],
        [InlineKeyboardButton("📄 إرسال ملف PDF", callback_data="pdf")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 **ميكانيك-AI** في خدمتك\n\n"
        "أنا الخبير المطلق في جميع المركبات.\n"
        "أرسل سؤالك مباشرة أو استخدم الأزرار.\n\n"
        "أدعم:\n"
        "- 📝 النص\n"
        "- 📸 الصور\n"
        "- 🎤 الصوت\n"
        "- 📄 المستندات",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # رسالة انتظار
    wait_msg = await update.message.reply_text("🔍 جاري التشخيص والبحث العميق...")
    
    # بحث جوجل للسياق
    search_results = deep_search_google(f"car repair diagnosis {user_message[:100]}")
    search_context = "\n".join(search_results[:3]) if search_results else ""
    
    # استعلام النموذج
    if search_context:
        full_query = f"باستخدام معلومات البحث هذه:\n{search_context}\n\nالسؤال: {user_message}"
    else:
        full_query = user_message
    
    response = query_model(full_query)
    
    # حفظ للتعلم
    save_conversation(user_id, user_message, response)
    
    # حذف رسالة الانتظار
    await wait_msg.delete()
    
    # إرسال الرد
    if len(response) > 4000:
        # تقسيم الرسائل الطويلة
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الصور"""
    user_id = update.effective_user.id
    
    wait_msg = await update.message.reply_text("📸 جاري تحليل الصورة...")
    
    # تنزيل الصورة
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"/tmp/vehicle_{user_id}.jpg"
    await photo_file.download_to_drive(photo_path)
    
    # تحليل الصورة
    image_description = analyze_image(photo_path)
    
    # الحصول على تعليق الصورة
    caption = update.message.caption or ""
    
    full_query = f"وصف الصورة: {image_description}\nتعليق المستخدم: {caption}\nشخص العطل وأعط الحل."
    response = query_model(full_query)
    
    save_conversation(user_id, f"[صورة] {caption}", response)
    
    await wait_msg.delete()
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الصوتية"""
    user_id = update.effective_user.id
    
    wait_msg = await update.message.reply_text("🎤 جاري تحويل الصوت إلى نص...")
    
    # تنزيل الصوت
    voice_file = await update.message.voice.get_file()
    voice_path = f"/tmp/voice_{user_id}.ogg"
    await voice_file.download_to_drive(voice_path)
    
    # تحويل إلى نص
    result = whisper_model.transcribe(voice_path)
    text = result["text"]
    
    # استعلام
    response = query_model(text)
    
    save_conversation(user_id, f"[صوت] {text}", response)
    
    await wait_msg.delete()
    
    # إرسال رد نصي وصوتي
    await update.message.reply_text(f"🗣 النص: {text}\n\n{response}")
    
    # تحويل الرد إلى صوت
    audio_path = f"/tmp/response_{user_id}.wav"
    tts.tts_to_file(text=response[:500], file_path=audio_path)
    
    with open(audio_path, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة المستندات"""
    user_id = update.effective_user.id
    document = update.message.document
    
    wait_msg = await update.message.reply_text("📄 جاري قراءة المستند...")
    
    # تنزيل
    doc_file = await document.get_file()
    doc_path = f"/tmp/doc_{user_id}_{document.file_name}"
    await doc_file.download_to_drive(doc_path)
    
    # استخراج النص من PDF
    try:
        from pypdf import PdfReader
        reader = PdfReader(doc_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    except:
        text = document.file_name
    
    # استعلام
    caption = update.message.caption or "حلل هذا المستند"
    response = query_model(f"محتوى المستند: {text[:2000]}\nالمطلوب: {caption}")
    
    save_conversation(user_id, f"[مستند] {caption}", response)
    
    await wait_msg.delete()
    await update.message.reply_text(response)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار القائمة"""
    query = update.callback_query
    await query.answer()
    
    prompts = {
        "diagnose": "كيف اشخص عطل في المركبة؟ اشرح الطريقة العلمية للتشخيص.",
        "maintenance": "ما هو جدول الصيانة الدورية الكامل للمركبات؟",
        "electrical": "كيف اشخص الأعطال الكهربائية في المركبة؟",
        "photo": "أرسل صورة للجزء المعطول وسأقوم بتشخيصه.",
        "voice": "أرسل رسالة صوتية تشرح فيها المشكلة.",
        "pdf": "أرسل ملف PDF لكتيب الصيانة أو تقرير الفحص."
    }
    
    prompt = prompts.get(query.data, "")
    if prompt:
        if query.data in ["photo", "voice", "pdf"]:
            await query.message.reply_text(prompt)
        else:
            response = query_model(prompt)
            await query.message.reply_text(response)

# === التشغيل ===

def main():
    """تشغيل البوت"""
    print("[*] تشغيل بوت ميكانيك-AI...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.DocumentCategory.PDF, handle_document))
    application.add_handler(CallbackQueryHandler(handle_button))
    
    print("[✓] البوت جاهز!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()