import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
client = OpenAI(api_key=API_KEY) if API_KEY else None

@app.get("/")
def root():
    return jsonify({
        "name": "NORYN AI Python Service",
        "version": "4.0.0",
        "status": "online",
        "ai": bool(client)
    })

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "python",
        "ai": bool(client)
    })

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "الرسالة فارغة."}), 400

    if not client:
        return jsonify({
            "error": "OPENAI_API_KEY غير مضبوط في Environment Variables."
        }), 503

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=(
                "أنت NORYN AI، مساعد ذكاء اصطناعي عربي متخصص في البرمجة. "
                "أجب بوضوح وساعد المستخدم في كتابة الأكواد وشرحها وتصحيحها. "
                "إذا طلب المستخدم كودًا، قدم كودًا منظمًا وقابلًا للاستخدام."
            ),
            input=message
        )
        return jsonify({
            "reply": response.output_text,
            "engine": MODEL
        })
    except Exception as error:
        print("OpenAI error:", error)
        return jsonify({
            "error": "حدث خطأ أثناء الاتصال بنموذج الذكاء الاصطناعي."
        }), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
