#!/usr/bin/env python3
"""تحميل وتهيئة النموذج الأساسي Llama 3.1 8B"""

import torch
from unsloth import FastLanguageModel
from transformers import AutoTokenizer

MODEL_PATH = "./models/llama-3-8b-mechanic"

def download_base_model():
    print("[*] تحميل النموذج الأساسي...")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Llama-3.1-8B-Instruct-bnb-4bit",
        max_seq_length=4096,
        dtype=None,
        load_in_4bit=True,
    )
    
    # إضافة LoRA للتدريب الفعال
    model = FastLanguageModel.get_peft_model(
        model,
        r=64,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )
    
    # حفظ
    model.save_pretrained(MODEL_PATH)
    tokenizer.save_pretrained(MODEL_PATH)
    
    print(f"[✓] النموذج محفوظ في: {MODEL_PATH}")
    return model, tokenizer

if __name__ == "__main__":
    download_base_model()