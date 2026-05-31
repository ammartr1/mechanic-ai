#!/bin/bash
# تشغيل ميكانيك-AI على كالي لينكس

echo "🔧 بدء تشغيل ميكانيك-AI..."
cd "$(dirname "$0")"

# تفعيل البيئة الافتراضية
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[-] إنشاء بيئة افتراضية..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install gradio schedule python-telegram-bot requests
fi

# التحقق من التوكن
if [ ! -f ".env" ]; then
    read -p "أدخل توكن بوت تيليجرام: " token
    echo "TELEGRAM_TOKEN=$token" > .env
fi

# تشغيل المكونات
echo "[*] تشغيل بوت تيليجرام..."
python3 bot/telegram_bot.py &
PID_BOT=$!

sleep 2

echo "[*] تشغيل واجهة الويب على http://localhost:7860"
python3 app.py &
PID_WEB=$!

echo ""
echo "========================================="
echo "   🔧 MECHANIC-AI يعمل بالكامل"
echo "   📱 تحقق من بوت تيليجرام"
echo "   🌐 http://localhost:7860"
echo "   PID Bot: $PID_BOT | PID Web: $PID_WEB"
echo "========================================="
echo ""
echo "اضغط Ctrl+C لإيقاف الجميع..."

# انتظار الإشارة
trap "kill $PID_BOT $PID_WEB 2>/dev/null; echo ' [✓] تم الإيقاف'; exit 0" SIGINT SIGTERM
wait
