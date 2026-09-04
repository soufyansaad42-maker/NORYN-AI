import os
from flask import Flask, request, jsonify
from huggingface_hub import InferenceClient

app = Flask(__name__)

# قراءة التوكن من Render Environment Variables
HF_TOKEN = os.environ.get("HF_TOKEN")

# النموذج المستخدم
MODEL = os.environ.get(
    "HF_MODEL",
    "deepseek-ai/DeepSeek-V3-0324"
)

# إنشاء عميل Hugging Face
client = InferenceClient(
    model=MODEL,
    token=HF_TOKEN
)


@app.get("/")
def home():
    return jsonify({
        "name": "NORYN AI Python Service",
        "version": "4.0.0",
        "status": "online",
        "ai": bool(HF_TOKEN),
        "model": MODEL
    })


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "python",
        "ai": bool(HF_TOKEN),
        "model": MODEL
    })


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "الرسالة فارغة."
        }), 400

    if not HF_TOKEN:
        return jsonify({
            "error": "HF_TOKEN غير موجود في Render."
        }), 503

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "أنت NORYN AI، مساعد ذكاء اصطناعي عربي متخصص "
                        "في البرمجة. ساعد المستخدم في إنشاء الأكواد "
                        "وشرحها وتصحيح الأخطاء وتحسينها. "
                        "أجب باللغة التي يستخدمها المستخدم."
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            max_tokens=1024,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        return jsonify({
            "reply": reply,
            "model": MODEL
        })

    except Exception as error:
        print("Hugging Face error:", error)

        return jsonify({
            "error": "حدث خطأ أثناء الاتصال بنموذج الذكاء الاصطناعي.",
            "details": str(error)
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
