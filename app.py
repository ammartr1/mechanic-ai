import gradio as gr
from llama_cpp import Llama
import os

SYSTEM_PROMPT = """أنت ميكانيك-AI، الخبير العالمي في جميع المركبات.
شخص العطل وأعط الحل المباشر دون تردد. أجب بالعربية."""

model_path = "./models/gguf/mechanic-ai-Q4_K_M.gguf"
if os.path.exists(model_path):
    llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4, verbose=False)
else:
    llm = None

def diagnose_vehicle(problem, model, year, additional_info):
    if llm is None:
        return "⚠️ النموذج غير محمل. يرجى تحميل ملف GGUF إلى مجلد models/gguf/"
    
    prompt = f"""<|system|>
{SYSTEM_PROMPT}
<|user|>
المركبة: {model} | السنة: {year}
المشكلة: {problem}
معلومات إضافية: {additional_info}
<|assistant|>"""
    
    response = llm(prompt, max_tokens=512, temperature=0.3, top_p=0.9)
    return response['choices'][0]['text'].strip()

def search_knowledge(problem, model, year):
    return diagnose_vehicle(problem, model, year, "")

with gr.Blocks(title="ميكانيك-AI | خبير المركبات") as demo:
    gr.Markdown("# 🔧 ميكانيك-AI | خبير المركبات المطلق")
    gr.Markdown("أدخل تفاصيل المشكلة للحصول على تشخيص دقيق وخطوات تصليح مباشرة")
    
    with gr.Row():
        with gr.Column(scale=2):
            problem = gr.Textbox(
                label="وصف المشكلة بالتفصيل",
                placeholder="مثال: المحرك يهتز عند التوقف، صوت طقطقة من الأمام، دخان أبيض من العادم...",
                lines=4
            )
            with gr.Row():
                model = gr.Textbox(label="موديل المركبة", placeholder="مثال: Toyota Camry")
                year = gr.Number(label="سنة الصنع", value=2020, precision=0)
            additional = gr.Textbox(label="معلومات إضافية (اختياري)", placeholder="عدد الكيلومترات، آخر صيانة...")
            
            submit_btn = gr.Button("🔍 تشخيص المشكلة", variant="primary", size="lg")
        
        with gr.Column(scale=2):
            output = gr.Textbox(label="التشخيص والحل", lines=15)
    
    submit_btn.click(
        fn=diagnose_vehicle,
        inputs=[problem, model, year, additional],
        outputs=output
    )
    
    gr.Examples(
        examples=[
            ["المحرك لا يدور عند إدارة المفتاح، فقط صوت طقة واحدة", "Honda Civic", 2018, "البطارية عمرها سنة"],
            ["صوت صفير عند الضغط على الفرامل", "BMW 320i", 2019, "تم تغيير الفرامل قبل شهرين"],
            ["تكييف السيارة يهرب هواء ساخن", "Mercedes C200", 2020, ""],
            ["الديزل يشتغل ويفصل مباشرة", "Ford F-150", 2021, "خزان الوقود ممتلئ"],
        ],
        inputs=[problem, model, year, additional]
    )

if __name__ == "__main__":
    demo.queue(max_size=20)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
