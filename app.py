import os
import traceback
from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient

app = Flask(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")
MODEL = os.environ.get("HF_MODEL", "deepseek-ai/DeepSeek-V3-0324")

client = InferenceClient(provider="auto", api_key=HF_TOKEN)

PROMPTS = {
    "code": "أنت NORYN AI، خبير متخصص في البرمجة. ساعد المستخدم في إنشاء الأكواد وتصحيحها وشرحها وتحسينها. أعطِ كودًا واضحًا ومنظمًا.",
    "learn": "أنت NORYN AI، مدرس ذكي. اشرح المعلومات بطريقة بسيطة ومنظمة ومناسبة للمبتدئين.",
    "write": "أنت NORYN AI، مساعد متخصص في الكتابة. ساعد المستخدم في كتابة وتنظيم وتحسين النصوص.",
    "general": "أنت NORYN AI، مساعد ذكاء اصطناعي عام. أجب عن أسئلة المستخدم بوضوح ودقة."
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "ai": bool(HF_TOKEN),
        "model": MODEL,
        "ok": True,
        "service": "NORYN AI",
        "version": "4.0.2"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    mode = str(data.get("mode", "general")).strip().lower()

    if not message:
        return jsonify({"ok": False, "error": "اكتب رسالة أولًا."}), 400

    if not HF_TOKEN:
        return jsonify({"ok": False, "error": "HF_TOKEN غير موجود في إعدادات Render."}), 500

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": PROMPTS.get(mode, PROMPTS["general"])},
                {"role": "user", "content": message}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        if not response or not getattr(response, "choices", None):
            return jsonify({"ok": False, "error": "النموذج لم يُرجع إجابة."}), 502

        message_obj = getattr(response.choices[0], "message", None)
        reply = getattr(message_obj, "content", None) if message_obj else None
        reply = str(reply or "").strip()

        if not reply:
            return jsonify({"ok": False, "error": "النموذج أرجع إجابة فارغة."}), 502

        return jsonify({
            "ok": True,
            "reply": reply,
            "model": MODEL,
            "mode": mode
        })

    except Exception as error:
        print("AI ERROR:", repr(error), flush=True)
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": "تعذر الحصول على رد من نموذج AI الآن. حاول مرة أخرى."
        }), 502

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "ok": False,
        "error": "حدث خطأ داخلي في NORYN AI."
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
