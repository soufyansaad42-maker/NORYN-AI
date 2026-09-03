from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify({
        "name": "NORYN AI Python Service",
        "version": "3.0.0",
        "status": "online"
    })

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "python"
    })

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "الرسالة فارغة."}), 400

    reply = (
        "تمت معالجة رسالتك بواسطة Python بنجاح! 🐍✅\n\n"
        f"رسالتك:\n{message}\n\n"
        "هذه استجابة تجريبية فقط. لم نربط نموذج AI حقيقي بعد. "
        "المرحلة التالية ستكون إضافة محرك/نموذج ذكاء اصطناعي حقيقي."
    )

    return jsonify({
        "reply": reply,
        "engine": "python"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
