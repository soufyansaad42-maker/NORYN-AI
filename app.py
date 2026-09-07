import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v7
# Flask + Hugging Face
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
except (TypeError, ValueError):
    MAX_TOKENS = 8192

try:
    TEMPERATURE = float(
        os.environ.get("HF_TEMPERATURE", "0.7")
    )
except (TypeError, ValueError):
    TEMPERATURE = 0.7

try:
    MAX_HISTORY_MESSAGES = int(
        os.environ.get(
            "HF_MAX_HISTORY_MESSAGES",
            "30"
        )
    )
except (TypeError, ValueError):
    MAX_HISTORY_MESSAGES = 30

try:
    MAX_HISTORY_CHARS = int(
        os.environ.get(
            "HF_MAX_HISTORY_CHARS",
            "50000"
        )
    )
except (TypeError, ValueError):
    MAX_HISTORY_CHARS = 50000


MAX_TOKENS = max(
    256,
    min(MAX_TOKENS, 16384)
)

TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)

MAX_HISTORY_MESSAGES = max(
    4,
    min(MAX_HISTORY_MESSAGES, 100)
)

MAX_HISTORY_CHARS = max(
    4000,
    min(MAX_HISTORY_CHARS, 120000)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN Base Personality
# =========================================================

BASE_PERSONALITY = """
أنت NORYN AI، مساعد ذكاء اصطناعي ذكي ومتعدد الاستخدامات.

مهمتك مساعدة المستخدم في:
- التعلم
- البرمجة
- الكتابة
- العلوم
- المعلومات العامة
- تحليل الأفكار
- حل المشكلات
- إنشاء المشاريع

قواعد المحادثة:

1. افهم سياق المحادثة السابقة.
2. لا تتعامل مع كل رسالة كأنها سؤال مستقل.
3. إذا قال المستخدم "اشرح الثانية"، ابحث عن المقصود في المحادثة السابقة.
4. إذا قال "تابع"، تابع الموضوع السابق.
5. إذا قال "أعدها"، أعد آخر شرح مناسب.
6. إذا قال "اختصرها"، اختصر الإجابة السابقة.
7. إذا قال "فصل أكثر"، قدم تفاصيل إضافية.
8. إذا قال "بالإنجليزية"، ترجم أو أعد الإجابة الأخيرة بالإنجليزية.
9. إذا قال "بالعربية"، أجب بالعربية.
10. لا تطلب من المستخدم إعادة معلومات سبق أن ذكرها في نفس المحادثة.
11. لا تدّعي أنك نفذت شيئًا لم تنفذه.
12. إذا لم تكن متأكدًا من معلومة، وضح ذلك.
13. لا تكرر الإجابة بلا سبب.
14. كن واضحًا وطبيعيًا.
15. اجعل طول الإجابة مناسبًا للسؤال.

اللغة:

- إذا كتب المستخدم بالعربية، أجب بالعربية.
- إذا طلب الإنجليزية، أجب بالإنجليزية.
- إذا طلب لغة أخرى، حاول الإجابة بها.
"""


# =========================================================
# Modes
# =========================================================

PROMPTS = {

    "general": BASE_PERSONALITY + """

أنت الآن في الوضع العام.

أجب عن:
- الأسئلة العامة
- العلوم
- التاريخ
- الجغرافيا
- التكنولوجيا
- المعلومات
- الأفكار
- التخطيط

نظم الإجابة عندما تحتاج إلى ذلك.
""",

    "code": BASE_PERSONALITY + """

أنت الآن NORYN AI في وضع البرمجة.

أنت متخصص في:

HTML5
CSS3
JavaScript
Python
Flask
Canvas
الألعاب
تطبيقات الويب
واجهات المستخدم
تصحيح الأخطاء
تحسين الأكواد

عند إنشاء كود:

1. قدم كودًا كاملًا.
2. لا تستخدم "..." بدل أجزاء من الكود.
3. لا تقل "أكمل الكود هنا".
4. أغلق جميع الأقواس.
5. أغلق جميع الدوال.
6. أغلق جميع HTML tags.
7. أكمل JavaScript.
8. إذا طلب المستخدم ملف HTML واحدًا، اجعل HTML وCSS وJavaScript في نفس الملف.
9. اجعل المشروع قابلًا للتشغيل مباشرة قدر الإمكان.
10. اجعل التصميم مناسبًا للهاتف إذا لم يحدد المستخدم غير ذلك.
11. استخدم JavaScript عاديًا إذا لم يطلب إطارًا معينًا.
12. ضع الكود داخل code fence مناسب.
13. اشرح طريقة التشغيل بعد الكود باختصار.
14. اجعل الكود أهم من الشرح الطويل.

قبل إرسال الكود راجعه منطقيًا.
""",

    "learn": BASE_PERSONALITY + """

أنت الآن مدرس ذكي.

عند شرح درس:

1. ابدأ بالمفهوم الأساسي.
2. استخدم لغة بسيطة.
3. قسم الدرس إلى أجزاء.
4. أعط أمثلة.
5. وضح الأخطاء الشائعة.
6. استخدم أسئلة قصيرة عند الحاجة.
7. إذا طلب المستخدم اختبارًا، أنشئ اختبارًا مناسبًا.
8. إذا أجاب المستخدم، صحح إجابته واشرح السبب.
9. إذا أخطأ المستخدم، وضح الخطأ بطريقة تعليمية.
10. إذا طلب إعادة الشرح، غير طريقة الشرح.

هدفك أن يفهم الطالب، وليس فقط أن يحصل على الإجابة.
""",

    "write": BASE_PERSONALITY + """

أنت الآن مساعد متخصص في الكتابة.

ساعد المستخدم في:
- القصص
- المقالات
- الأفكار
- التلخيص
- إعادة الصياغة
- الرسائل
- الوصف
- المحتوى الإبداعي

إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة.
إذا طلب تحسين نص، حافظ على المعنى وحسن الأسلوب.
"""
}


# =========================================================
# Code Detection
# =========================================================

CODE_KEYWORDS = [
    "اكتب كود",
    "أعطني كود",
    "اعطني كود",
    "أنشئ كود",
    "اصنع كود",
    "اكتب لعبة",
    "أنشئ لعبة",
    "اصنع لعبة",
    "لعبة html",
    "ملف html",
    "صفحة html",
    "html",
    "css",
    "javascript",
    "python",
    "flask",
    "canvas",
    "برمج",
    "برمجة",
    "كود كامل",
    "مشروع",
    "website",
    "web app",
    "code",
    "game"
]


def is_code_request(message, mode):
    if mode == "code":
        return True

    text = message.lower()

    return any(
        keyword.lower() in text
        for keyword in CODE_KEYWORDS
    )


# =========================================================
# Code Instructions
# =========================================================

CODE_INSTRUCTIONS = """

هذه الرسالة مرتبطة بالبرمجة.

قبل إرسال الإجابة:

- لا تقطع الكود.
- لا تستخدم ...
- لا تترك دوال ناقصة.
- أغلق الأقواس.
- أغلق HTML tags.
- أكمل JavaScript.
- تأكد من IDs.
- تأكد من أسماء الدوال.
- إذا طلب ملفًا واحدًا، أرسل ملفًا واحدًا كاملًا.
- اجعل الكود قابلًا للتشغيل قدر الإمكان.
- لا تضع شرحًا طويلًا داخل الكود.
"""


# =========================================================
# Clean Text
# =========================================================

def clean_text(value, default=""):
    if value is None:
        return default

    return str(value).strip()


# =========================================================
# Mode Prompt
# =========================================================

def get_mode_prompt(mode):

    mode = clean_text(
        mode,
        "general"
    ).lower()

    return PROMPTS.get(
        mode,
        PROMPTS["general"]
    )


# =========================================================
# Build Conversation
# =========================================================

def build_messages(
    system_prompt,
    history,
    current_message
):

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if not isinstance(history, list):
        history = []

    cleaned = []

    for item in history:

        if not isinstance(item, dict):
            continue

        message_type = clean_text(
            item.get("type")
        ).lower()

        text = clean_text(
            item.get("text")
        )

        if not text:
            continue

        if message_type == "user":

            cleaned.append({
                "role": "user",
                "content": text
            })

        elif message_type in (
            "ai",
            "assistant"
        ):

            cleaned.append({
                "role": "assistant",
                "content": text
            })

    # آخر الرسائل أهم للسياق
    cleaned = cleaned[
        -MAX_HISTORY_MESSAGES:
    ]

    # تحديد الحجم
    selected = []
    total_chars = 0

    for item in reversed(cleaned):

        text = item["content"]
        size = len(text)

        if (
            selected
            and
            total_chars + size > MAX_HISTORY_CHARS
        ):
            break

        selected.append(item)
        total_chars += size

    selected.reverse()

    messages.extend(selected)

    # السؤال الحالي
    messages.append({
        "role": "user",
        "content": current_message
    })

    return messages


# =========================================================
# Extract Reply
# =========================================================

def extract_reply(response):

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

    except Exception as error:

        print(
            "NORYN extract error:",
            repr(error),
            flush=True
        )

        return ""


# =========================================================
# Home
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# Health
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "ok": True,

        "ai": bool(HF_TOKEN),

        "model": MODEL,

        "service": "NORYN AI",

        "version": "7.0",

        "memory": True,

        "context": True,

        "max_tokens": MAX_TOKENS,

        "history_messages":
            MAX_HISTORY_MESSAGES,

        "history_chars":
            MAX_HISTORY_CHARS
    })


# =========================================================
# Chat API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    message = clean_text(
        data.get("message")
    )

    mode = clean_text(
        data.get(
            "mode",
            "general"
        ),
        "general"
    ).lower()

    history = data.get(
        "history",
        []
    )


    # -----------------------------------------------------
    # Validate mode
    # -----------------------------------------------------

    if mode not in PROMPTS:
        mode = "general"


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
            "error":
                "HF_TOKEN غير موجود في إعدادات Render."
        }), 500


    # -----------------------------------------------------
    # Message length
    # -----------------------------------------------------

    if len(message) > 40000:

        return jsonify({
            "ok": False,
            "error":
                "الرسالة طويلة جدًا. حاول تقليل حجمها."
        }), 413


    # -----------------------------------------------------
    # System prompt
    # -----------------------------------------------------

    system_prompt = get_mode_prompt(
        mode
    )


    # -----------------------------------------------------
    # Code enhancement
    # -----------------------------------------------------

    if is_code_request(
        message,
        mode
    ):

        system_prompt += CODE_INSTRUCTIONS


    # -----------------------------------------------------
    # Build messages
    # -----------------------------------------------------

    messages = build_messages(
        system_prompt,
        history,
        message
    )


    # -----------------------------------------------------
    # Logs
    # -----------------------------------------------------

    print(
        "\n========== NORYN v7 ==========",
        flush=True
    )

    print(
        "Model:",
        MODEL,
        flush=True
    )

    print(
        "Mode:",
        mode,
        flush=True
    )

    print(
        "Context messages:",
        len(messages) - 2,
        flush=True
    )

    print(
        "Message length:",
        len(message),
        flush=True
    )

    print(
        "==============================\n",
        flush=True
    )


    # =====================================================
    # Hugging Face
    # =====================================================

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        # -------------------------------------------------
        # Extract reply
        # -------------------------------------------------

        reply = extract_reply(
            response
        )


        # -------------------------------------------------
        # Empty response
        # -------------------------------------------------

        if not reply:

            return jsonify({

                "ok": False,

                "error":
                    "النموذج لم يُرجع إجابة."

            }), 502


        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return jsonify({

            "ok": True,

            "reply": reply,

            "model": MODEL,

            "mode": mode,

            "version": "7.0",

            "memory": True,

            "context_messages":
                len(messages) - 2

        })


    except Exception as error:

        print(
            "\n========== NORYN ERROR ==========",
            flush=True
        )

        print(
            repr(error),
            flush=True
        )

        traceback.print_exc()

        print(
            "=================================\n",
            flush=True
        )

        return jsonify({

            "ok": False,

            "error":
                "تعذر الحصول على إجابة من NORYN AI الآن. "
                "تحقق من Render Logs."

        }), 502


# =========================================================
# Error 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "ok": False,

        "error":
            "المسار غير موجود."

    }), 404


# =========================================================
# Error 405
# =========================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "ok": False,

        "error":
            "طريقة الطلب غير مسموحة."

    }), 405


# =========================================================
# Error 500
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

        "error":
            "حدث خطأ داخلي في الخادم."

    }), 500


# =========================================================
# Start
# =========================================================

if __name__ == "__main__":

    try:

        port = int(
            os.environ.get(
                "PORT",
                "8000"
            )
        )

    except (TypeError, ValueError):

        port = 8000


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
