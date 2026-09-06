import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v4.2
# Flask + Hugging Face InferenceClient
# =========================================================

app = Flask(__name__)


# =========================================================
# Environment
# =========================================================

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()

MODEL = os.environ.get(
    "HF_MODEL",
    "deepseek-ai/DeepSeek-V3-0324"
).strip()

try:
    MAX_TOKENS = int(
        os.environ.get("HF_MAX_TOKENS", "8192")
    )
except ValueError:
    MAX_TOKENS = 8192

try:
    TEMPERATURE = float(
        os.environ.get("HF_TEMPERATURE", "0.7")
    )
except ValueError:
    TEMPERATURE = 0.7


# حماية القيم
MAX_TOKENS = max(256, min(MAX_TOKENS, 16384))
TEMPERATURE = max(0.0, min(TEMPERATURE, 2.0))


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN AI Modes
# =========================================================

PROMPTS = {

    "general": """
أنت NORYN AI، مساعد ذكاء اصطناعي عام وذكي.

مهمتك:
- الإجابة عن الأسئلة العامة.
- مساعدة المستخدم في الدراسة والتعلم.
- تقديم الأفكار والاقتراحات.
- شرح المواضيع بطريقة واضحة.
- المساعدة في التخطيط والتنظيم.
- المساعدة في الكتابة.
- المساعدة في البرمجة عند الطلب.

القواعد:
- أجب باللغة العربية عندما يكتب المستخدم بالعربية.
- إذا استخدم المستخدم لغة أخرى، يمكنك الإجابة بلغته.
- لا تكن مطولًا بلا سبب.
- إذا كان السؤال يحتاج شرحًا، استخدم عناوين ونقاط.
- لا تدّعي أنك نفذت شيئًا لم تنفذه.
- إذا لم تكن متأكدًا من معلومة، وضح ذلك.
""",

    "code": """
أنت NORYN AI، مساعد برمجة احترافي.

تخصصك:
- HTML5
- CSS3
- JavaScript
- Python
- Flask
- واجهات الويب
- الألعاب باستخدام Canvas
- تصحيح الأخطاء
- تحسين الأكواد
- شرح الأكواد
- تصميم المشاريع

عند طلب إنشاء كود:

1. افهم المطلوب بدقة.
2. أعطِ كودًا كاملًا وقابلًا للتشغيل قدر الإمكان.
3. لا تقطع الكود.
4. لا تستخدم:
   "أكمل الكود هنا"
   أو
   "..."
   بدل أجزاء الكود المطلوبة.
5. إذا طلب المستخدم ملف HTML واحدًا، ضع HTML وCSS وJavaScript داخله.
6. إذا طلب لعبة HTML، اجعلها قابلة للتشغيل مباشرة في المتصفح.
7. اجعل التصميم Mobile First إذا لم يحدد المستخدم غير ذلك.
8. استخدم JavaScript عاديًا بدون React أو Vue أو Angular ما لم يطلب المستخدم ذلك.
9. استخدم code fences صحيحة.
10. بعد الكود، قدم شرحًا مختصرًا لطريقة التشغيل.
11. لا تضع شرحًا طويلًا داخل كتلة الكود.
12. راجع الأقواس والدوال والوسوم قبل إنهاء الإجابة.
13. عندما تنشئ لعبة، اجعل نقطة البداية والأزرار والتحكم واضحة.
14. إذا كان المطلوب ملفًا واحدًا، لا تقسمه إلى ملفات متعددة.
15. الأولوية للكود الكامل والصحيح، وليس للشرح الطويل.

مهم جدًا:
إذا كان الكود طويلًا، قلّل الشرح أولًا وحافظ على الكود.
لا تتوقف في منتصف HTML أو CSS أو JavaScript.
""",

    "learn": """
أنت NORYN AI، مدرس ذكي.

مهمتك:
- تعليم المستخدم بطريقة بسيطة.
- شرح المواضيع خطوة بخطوة.
- تقسيم الموضوع إلى أجزاء صغيرة.
- إعطاء أمثلة عند الحاجة.
- عدم افتراض أن المستخدم خبير.
- استخدام أمثلة عملية.
- استخدام العربية الواضحة عندما يكون السؤال بالعربية.

إذا كان الموضوع صعبًا:
ابدأ بالفكرة الأساسية ثم انتقل إلى التفاصيل.
""",

    "write": """
أنت NORYN AI، مساعد متخصص في الكتابة.

ساعد المستخدم في:
- القصص.
- المقالات.
- الأفكار.
- التلخيص.
- إعادة الصياغة.
- الرسائل.
- الوصف.
- المحتوى الإبداعي.

اكتب بأسلوب طبيعي ومنظم.

إذا طلب المستخدم نصًا جاهزًا:
أعطه النص مباشرة دون شرح زائد.
"""
}


# =========================================================
# Helpers
# =========================================================

def clean_text(value, default=""):
    """تحويل القيمة إلى نص آمن."""
    if value is None:
        return default

    return str(value).strip()


def get_mode_prompt(mode):
    """الحصول على System Prompt المناسب."""
    mode = clean_text(mode, "general").lower()

    return PROMPTS.get(
        mode,
        PROMPTS["general"]
    )


def is_code_request(message):
    """اكتشاف طلبات البرمجة والأكواد."""

    keywords = [
        "اكتب كود",
        "أنشئ كود",
        "اصنع كود",
        "كود كامل",
        "أنشئ لعبة",
        "اصنع لعبة",
        "اكتب لعبة",
        "لعبة html",
        "ملف html",
        "html",
        "css",
        "javascript",
        "javascript",
        "python",
        "flask",
        "canvas",
        "برمج",
        "برمجة",
        "كود"
    ]

    text = message.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def extract_reply(response):
    """استخراج نص الإجابة من Hugging Face."""

    if not response:
        return ""

    try:
        choices = getattr(
            response,
            "choices",
            None
        )

        if not choices:
            return ""

        first = choices[0]

        message = getattr(
            first,
            "message",
            None
        )

        if message is None:
            return ""

        content = getattr(
            message,
            "content",
            None
        )

        if content is None:
            return ""

        return str(content).strip()

    except Exception:
        return ""


# =========================================================
# Home
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# Health Check
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "ok": True,
        "ai": bool(HF_TOKEN),
        "model": MODEL,
        "service": "NORYN AI",
        "version": "4.2",
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE
    })


# =========================================================
# Chat API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    # -----------------------------------------------------
    # Read JSON
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    message = clean_text(
        data.get("message")
    )

    mode = clean_text(
        data.get("mode"),
        "general"
    ).lower()


    # -----------------------------------------------------
    # Validate message
    # -----------------------------------------------------

    if not message:

        return jsonify({
            "ok": False,
            "error": "اكتب رسالة أولًا."
        }), 400


    # -----------------------------------------------------
    # Validate token
    # -----------------------------------------------------

    if not HF_TOKEN:

        return jsonify({
            "ok": False,
            "error": "HF_TOKEN غير موجود في إعدادات Render."
        }), 500


    # -----------------------------------------------------
    # Input limit
    # -----------------------------------------------------

    if len(message) > 30000:

        return jsonify({
            "ok": False,
            "error": "الرسالة طويلة جدًا. حاول تقليل حجمها."
        }), 413


    # -----------------------------------------------------
    # System Prompt
    # -----------------------------------------------------

    system_prompt = get_mode_prompt(mode)


    # -----------------------------------------------------
    # Code Request Enhancement
    # -----------------------------------------------------

    if is_code_request(message):

        system_prompt += """

هذه الرسالة مرتبطة بالبرمجة أو إنشاء مشروع.

قبل إرسال الإجابة النهائية:

- تأكد من اكتمال الكود.
- لا تتوقف في منتصف الكود.
- أغلق جميع HTML tags.
- أغلق جميع الأقواس { }.
- أغلق جميع الأقواس ( ).
- أغلق جميع الأقواس [ ].
- أكمل جميع الدوال.
- أكمل جميع المتغيرات المطلوبة.
- لا تستبدل الكود بـ "...".
- لا تقل "أكمل الباقي بنفس الطريقة".
- إذا كان المطلوب ملف HTML واحدًا، أعطِ ملف HTML واحدًا كاملًا.
- اجعل JavaScript داخل <script>.
- اجعل CSS داخل <style> إذا كان المطلوب ملفًا واحدًا.
- تأكد أن اللعبة أو التطبيق يبدأ بطريقة واضحة.
- اجعل أزرار الهاتف والتحكم باللمس موجودة عندما يكون ذلك مناسبًا.

الأولوية القصوى:
إرسال الكود الكامل قبل الشرح.
"""


    # -----------------------------------------------------
    # Request Hugging Face
    # -----------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE,

            top_p=0.95
        )


        # -------------------------------------------------
        # Extract Reply
        # -------------------------------------------------

        reply = extract_reply(response)


        if not reply:

            print(
                "NORYN ERROR: Empty model response",
                flush=True
            )

            return jsonify({
                "ok": False,
                "error": "النموذج لم يُرجع إجابة."
            }), 502


        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return jsonify({

            "ok": True,

            "reply": reply,

            "model": MODEL,

            "mode": mode,

            "version": "4.2"

        })


    # -----------------------------------------------------
    # Error
    # -----------------------------------------------------

    except Exception as error:

        print(
            "\n========== NORYN AI ERROR ==========",
            flush=True
        )

        print(
            repr(error),
            flush=True
        )

        traceback.print_exc()

        print(
            "====================================\n",
            flush=True
        )


        return jsonify({

            "ok": False,

            "error":
                "تعذر الحصول على إجابة من NORYN AI الآن. "
                "تحقق من Render Logs."

        }), 502


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "ok": False,

        "error": "المسار غير موجود."

    }), 404


# =========================================================
# 405
# =========================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "ok": False,

        "error": "طريقة الطلب غير مسموحة."

    }), 405


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    print(
        "NORYN INTERNAL ERROR:",
        repr(error),
        flush=True
    )

    return jsonify({

        "ok": False,

        "error": "حدث خطأ داخلي في الخادم."

    }), 500


# =========================================================
# Local / Render
# =========================================================

if __name__ == "__main__":

    try:
        port = int(
            os.environ.get(
                "PORT",
                "8000"
            )
        )
    except ValueError:
        port = 8000

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
