#!/usr/bin/env python3
"""تدريب نموذج ميكانيك-AI على بيانات المركبات"""

import json
import torch
from datasets import Dataset
from unsloth import FastLanguageModel, is_bfloat16_supported
from trl import SFTTrainer
from transformers import TrainingArguments
import pandas as pd

# تحميل بيانات التدريب
with open("./data/vehicle_knowledge.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# تنسيق البيانات للتدريب
training_data = []
for item in raw_data:
    training_data.append({
        "instruction": "أنت خبير تشخيص ميكانيكي وكهربائي للمركبات والشاحنات والآليات. أجب بدقة وثقة واعط الحل المباشر.",
        "input": f"السؤال: {item.get('title', '')}",
        "output": item.get("content", "")[:2000]
    })

# تحويل إلى Dataset
dataset = Dataset.from_list(training_data[:5000])

# تحميل النموذج
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./models/llama-3-8b-mechanic",
    max_seq_length=4096,
    dtype=None,
    load_in_4bit=True,
)

# إعدادات التدريب
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=4096,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=500,
        learning_rate=2e-4,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="./training/outputs",
        save_strategy="steps",
        save_steps=100,
    ),
)

# تدريب
print("[*] بدء التدريب...")
trainer.train()

# حفظ النموذج المدرب
print("[*] حفظ النموذج المدرب...")
model.save_pretrained("./models/mechanic-ai-final")
tokenizer.save_pretrained("./models/mechanic-ai-final")
print("[✓] اكتمل التدريب!")