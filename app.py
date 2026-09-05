import os
from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
MODEL = os.environ.get("HF_MODEL", "deepseek-ai/DeepSeek-V3-0324")

client = InferenceClient(
    model=MODEL,
    token=HF_TOKEN
)

PROMPTS = {
    "code": """أنت NORYN AI، خبير متخصص في البرمجة. ساعد المستخدم في إنشاء الأكواد وتصحيحها وشرحها وتحسينها. أعطِ كودًا واضحًا ومنظمًا.""",
    "learn": """أنت NORYN AI، مدرس ذكي. اشرح المعلومات بطريقة بسيطة ومنظمة ومناسبة للمبتدئين.""",
    "write": """أنت NORYN AI، مساعد متخصص في الكتابة. ساعد المستخدم في كتابة وتنظيم وتحسين النصوص.""",
    "general": """أنت NORYN AI، مساعد ذكاء اصطناعي عام. أجب عن أسئلة المستخدم بوضوح ودقة."""
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "NORYN AI",
        "version": "4.0.0",
        "ai": bool(HF_TOKEN),
        "model": MODEL
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    mode = str(data.get("mode", "general")).strip()

    if not message:
        return jsonify({"ok": False, "error": "اكتب رسالة أولًا."}), 400

    if not HF_TOKEN:
        return jsonify({"ok": False, "error": "HF_TOKEN غير موجود."}), 500

    system_prompt = PROMPTS.get(mode, PROMPTS["general"])

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        return jsonify({
            "ok": True,
            "reply": reply,
            "model": MODEL,
            "mode": mode
        })

    except Exception as error:
        print("AI ERROR:", error)
        return jsonify({
            "ok": False,
            "error": "حدث خطأ أثناء الاتصال بنموذج AI."
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
