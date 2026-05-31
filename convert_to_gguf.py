#!/usr/bin/env python3
"""تحويل النموذج إلى صيغة GGUF للتشغيل على CPU"""

import subprocess
import os

MODEL_DIR = "./models/mechanic-ai-final"
OUTPUT_DIR = "./models/gguf"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# تحويل باستخدام llama.cpp
commands = [
    f"python llama.cpp/convert.py {MODEL_DIR} --outfile {OUTPUT_DIR}/mechanic-ai-fp16.gguf --outtype f16",
    f"llama.cpp/quantize {OUTPUT_DIR}/mechanic-ai-fp16.gguf {OUTPUT_DIR}/mechanic-ai-Q4_K_M.gguf Q4_K_M"
]

for cmd in commands:
    print(f"[*] تنفيذ: {cmd}")
    subprocess.run(cmd, shell=True)

print(f"[✓] النموذج جاهز في: {OUTPUT_DIR}")