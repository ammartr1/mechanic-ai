#!/usr/bin/env python3
"""نظام التعلم الذاتي - يجمع المحادثات ويعيد تدريب النموذج تلقائياً"""

import sqlite3
import json
import subprocess
from datetime import datetime, timedelta
import schedule
import time

DATABASE_PATH = "./data/chat_logs.db"
TRAINING_SCRIPT = "./train_model.py"

def collect_new_conversations():
    """جمع المحادثات الجديدة"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # جمع محادثات آخر 7 أيام
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT message, response FROM conversations WHERE timestamp > ?", (week_ago,))
    
    conversations = cursor.fetchall()
    conn.close()
    
    # تحويل إلى تنسيق التدريب
    training_data = []
    for msg, resp in conversations:
        if len(msg) > 20 and len(resp) > 50:  # تجاهل القصيرة
            training_data.append({
                "instruction": "أنت خبير تشخيص ميكانيكي وكهربائي للمركبات. أجب بدقة وثقة.",
                "input": msg,
                "output": resp
            })
    
    # حفظ
    with open("./data/new_training_data.json", "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print(f"[*] تم جمع {len(training_data)} محادثة جديدة للتدريب")
    return len(training_data)

def retrain_model():
    """إعادة تدريب النموذج"""
    count = collect_new_conversations()
    
    if count > 50:  # تدريب فقط إذا كان هناك بيانات كافية
        print(f"[*] بدء إعادة التدريب بـ {count} محادثة...")
        subprocess.run(["python", TRAINING_SCRIPT, "--new-data"])
        print("[✓] اكتمل التدريب الذاتي!")
    else:
        print(f"[*] بيانات غير كافية ({count} محادثة). في الانتظار...")

# جدولة التدريب كل أحد
schedule.every().sunday.at("03:00").do(retrain_model)

if __name__ == "__main__":
    print("[*] نظام التعلم الذاتي قيد التشغيل...")
    print("[*] سيتم التدريب تلقائياً كل يوم أحد الساعة 3 صباحاً")
    
    # تشغيل أولي
    retrain_model()
    
    while True:
        schedule.run_pending()
        time.sleep(3600)