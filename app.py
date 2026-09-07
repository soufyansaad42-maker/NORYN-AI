```python
import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v6
# Backend
# Flask + Hugging Face InferenceClient
#
# Features:
# - Conversation memory
# - General / Code / Learn / Write modes
# - Long conversation history
# - Better code generation
# - Arabic / English support
# - Automatic conversation context
# - Error handling
# - Health endpoint
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

MAX_TOKENS = int(
    os.environ.get(
        "HF_MAX_TOKENS",
        "8192"
    )
)

TEMPERATURE = float(
    os.environ.get(
        "HF_TEMPERATURE",
        "0.7"
    )
)


# حماية القيم
MAX_TOKENS = max(
    512,
    min(MAX_TOKENS, 16384)
)

TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)


# الحد الأقصى لعدد رسائل الذاكرة
MAX_HISTORY_MESSAGES = int(
    os.environ.get(
        "NORYN_MAX_HISTORY",
        "30"
    )
)

MAX_HISTORY_MESSAGES = max(
    4,
    min(MAX_HISTORY_MESSAGES, 60)
)


# الحد الأقصى لطول الرسالة الواحدة
MAX_MESSAGE_LENGTH = 30000


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN Modes
# =========================================================

PROMPTS = {

    "general": """
أنت NORYN AI، مساعد ذكاء اصطناعي عام وذكي.

مهمتك:
- الإجابة عن الأسئلة العامة.
- شرح المعلومات بطريقة واضحة.
- مساعدة المستخدم في التعلم.
- تقديم الأفكار والاقتراحات.
- المساعدة في التخطيط والتنظيم.
- المساعدة في الكتابة.
- المساعدة في البرمجة عند الطلب.

القواعد:
- أجب باللغة التي يستخدمها المستخدم.
- إذا كتب المستخدم بالعربية فأجب بالعربية.
- إذا طلب الإنجليزية فأجب بالإنجليزية.
- إذا طلب لغة محددة فاستخدمها.
- لا تكن مطولًا بلا سبب.
- إذا كان السؤال يحتاج شرحًا، استخدم العناوين والنقاط والأمثلة.
- لا تدّع أنك نفذت شيئًا لم تنفذه.
- إذا لم تكن متأكدًا من معلومة، وضّح ذلك.
- حافظ على سياق المحادثة السابقة.
- إذا كان سؤال المستخدم تابعًا لسؤال سابق، اربطه بالسياق السابق.
""",

    "code": """
أنت NORYN AI، مساعد برمجة احترافي.

متخصص في:
HTML5
CSS3
JavaScript
Python
Flask
Canvas
الألعاب
واجهات الويب
تصحيح الأخطاء
تحسين الأكواد
تصميم المشاريع
شرح الأكواد

عند إنشاء كود:

1. افهم المطلوب أولًا.
2. أعطِ كودًا كاملًا قدر الإمكان.
3. لا تقطع الكود في منتصفه.
4. لا تستخدم "..." بدل أجزاء الكود.
5. إذا طلب المستخدم ملف HTML واحدًا، ضع HTML وCSS وJavaScript في نفس الملف.
6. اجعل المشاريع قابلة للتشغيل مباشرة قدر الإمكان.
7. اجعل التصميم مناسبًا للهاتف إذا لم يحدد المستخدم غير ذلك.
8. استخدم JavaScript عاديًا إذا لم يطلب المستخدم إطار عمل.
9. أغلق جميع HTML tags.
10. أغلق جميع الأقواس.
11. أكمل جميع الدوال.
12. راجع الكود قبل إرساله.
13. إذا كان الكود طويلًا جدًا، قلّل الشرح وليس الكود.
14. ضع الكود داخل code fence مناسب.
15. بعد الكود أعطِ شرحًا مختصرًا وطريقة التشغيل.
16. إذا طلب المستخدم تعديل كود سابق، حافظ على ما يعمل وأصلح الجزء المطلوب فقط.
17. تذكر سياق المشروع والأكواد السابقة في المحادثة.

الأولوية:
الكود الكامل والصحيح أهم من الشرح الطويل.
""",

    "learn": """
أنت NORYN AI، مدرس ذكي.

مهمتك:
- تعليم المستخدم بطريقة بسيطة.
- شرح المواضيع خطوة بخطوة.
- تقسيم الدرس إلى أجزاء صغيرة.
- إعطاء أمثلة.
- طرح أسئلة قصيرة للتأكد من الفهم عند الحاجة.
- تصحيح إجابات الطالب بطريقة واضحة.
- عدم افتراض أن المستخدم خبير.
- الانتقال من الأساسيات إلى التفاصيل.
- ربط الدرس بالأسئلة السابقة.
- إذا طلب المستخدم اختبارًا، أنشئ اختبارًا مناسبًا للموضوع.
- إذا أجاب المستخدم عن سؤال سابق، قيّم إجابته أولًا ثم تابع.

استخدم اللغة التي يطلبها المستخدم.
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

القواعد:
- اكتب بأسلوب طبيعي ومنظم.
- إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة.
- لا تضف شرحًا طويلًا إذا لم يطلبه.
- حافظ على الأسلوب المطلوب.
- تذكر السياق السابق للمحادثة.
"""
}


# =========================================================
# Helpers
# =========================================================

def clean_text(value, default=""):
    """
    تحويل القيمة إلى نص آمن.
    """
    if value is None:
        return default

    return str(value).strip()


def get_mode_prompt(mode):
    """
    الحصول على Prompt المناسب.
    """

    mode = clean_text(
        mode,
        "general"
    ).lower()

    return PROMPTS.get(
        mode,
        PROMPTS["general"]
    )


def extract_reply(response):
    """
    استخراج نص الإجابة من Hugging Face.
    """

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


def build_messages(
    system_prompt,
    history,
    current_message
):
    """
    بناء سجل المحادثة الذي سيرسل للنموذج.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if not isinstance(history, list):
        history = []

    # تنظيف التاريخ
    cleaned_history = []

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

            cleaned_history.append({
                "role": "user",
                "content": text
            })

        elif message_type == "ai":

            cleaned_history.append({
                "role": "assistant",
                "content": text
            })

    # نأخذ آخر عدد مناسب من الرسائل
    cleaned_history = cleaned_history[
        -MAX_HISTORY_MESSAGES:
    ]

    messages.extend(
        cleaned_history
    )

    # الرسالة الحالية
    messages.append({
        "role": "user",
        "content": current_message
    })

    return messages


def looks_like_code_request(message):
    """
    اكتشاف طلبات البرمجة.
    """

    keywords = [
        "اكتب كود",
        "أنشئ كود",
        "اعطني كود",
        "أعطني كود",
        "اصنع لعبة",
        "أنشئ لعبة",
        "لعبة",
        "كود كامل",
        "ملف html",
        "html",
        "css",
        "javascript",
        "javascript",
        "python",
        "flask",
        "برمج",
        "برمجة",
        "website",
        "web app",
        "code",
        "coding"
    ]

    message_lower = message.lower()

    return any(
        keyword.lower() in message_lower
        for keyword in keywords
    )


def add_code_instruction(system_prompt):
    """
    تعليمات إضافية لطلبات البرمجة.
    """

    return system_prompt + """

هذه الرسالة تبدو مرتبطة بالبرمجة.

قبل إرسال الإجابة:
- راجع الكود.
- لا تقطع الكود.
- لا تستبدل أجزاء مطلوبة بـ "...".
- أغلق الأقواس.
- أغلق الوسوم.
- أكمل الدوال.
- تأكد من أن JavaScript مكتمل.
- إذا كان المطلوب ملفًا واحدًا فأرسله كاملًا.
- اجعل الكود مناسبًا للتشغيل مباشرة.
"""


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

        "version": "6",

        "max_tokens": MAX_TOKENS,

        "history_messages":
            MAX_HISTORY_MESSAGES

    })


# =========================================================
# Chat API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
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
    # Validate message
    # -----------------------------------------------------

    if not message:

        return jsonify({

            "ok": False,

            "error":
                "اكتب رسالة أولًا."

        }), 400


    if len(message) > MAX_MESSAGE_LENGTH:

        return jsonify({

            "ok": False,

            "error":
                "الرسالة طويلة جدًا. حاول تقليل حجمها."

        }), 413


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
    # Mode
    # -----------------------------------------------------

    system_prompt = get_mode_prompt(
        mode
    )


    # -----------------------------------------------------
    # Code detection
    # -----------------------------------------------------

    if looks_like_code_request(
        message
    ):

        system_prompt = add_code_instruction(
            system_prompt
        )


    # -----------------------------------------------------
    # Build conversation
    # -----------------------------------------------------

    messages = build_messages(

        system_prompt,

        history,

        message

    )


    # -----------------------------------------------------
    # Call Hugging Face
    # -----------------------------------------------------

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


        if not reply:

            print(
                "NORYN ERROR: Empty model response",
                flush=True
            )

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

            "version": "6"

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

        "error":
            "المسار غير موجود."

    }), 404


# =========================================================
# 405
# =========================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "ok": False,

        "error":
            "طريقة الطلب غير مسموحة."

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

        "error":
            "حدث خطأ داخلي في الخادم."

    }), 500


# =========================================================
# Local / Render
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "8000"
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
```
