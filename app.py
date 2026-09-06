import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v4.3
# Backend: Flask + Hugging Face InferenceClient
#
# Features:
# - General AI
# - Programming mode
# - Learning mode
# - Writing mode
# - Conversation memory
# - Long code generation
# - Mobile-friendly projects
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
    os.environ.get("HF_MAX_TOKENS", "8192")
)

TEMPERATURE = float(
    os.environ.get("HF_TEMPERATURE", "0.7")
)

# عدد رسائل المحادثة التي نسمح بإرسالها للنموذج
# لتجنب تضخم الطلبات مع المحادثات الطويلة.
MAX_HISTORY_MESSAGES = int(
    os.environ.get("HF_MAX_HISTORY", "20")
)

# حماية من القيم غير المناسبة
MAX_TOKENS = max(
    256,
    min(MAX_TOKENS, 16384)
)

TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)

MAX_HISTORY_MESSAGES = max(
    2,
    min(MAX_HISTORY_MESSAGES, 50)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN AI Personalities
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
- كن واضحًا ومفيدًا.
- لا تكن مطولًا بلا سبب.
- إذا كان السؤال يحتاج شرحًا، استخدم العناوين والنقاط والأمثلة.
- لا تدّعي أنك نفذت شيئًا لم تنفذه.
- إذا لم تكن متأكدًا من معلومة، وضّح ذلك.
- حافظ على سياق المحادثة السابقة.
- إذا قال المستخدم "هذا" أو "السابق" أو "الكود السابق"، حاول فهم المقصود من الرسائل السابقة.
""",

    "code": """
أنت NORYN AI، مساعد برمجة احترافي.

أنت متخصص في:
HTML5
CSS3
JavaScript
Python
Flask
واجهات الويب
الألعاب باستخدام Canvas
تصحيح الأخطاء
تحسين الأكواد
شرح الأكواد
تصميم المشاريع

عند طلب إنشاء كود:

1. افهم المطلوب أولًا.
2. أعطِ كودًا كاملًا وقابلًا للتشغيل قدر الإمكان.
3. لا تقطع الكود في منتصفه.
4. لا تستخدم "..." بدل أجزاء مطلوبة.
5. إذا طلب المستخدم ملف HTML واحدًا، ضع HTML وCSS وJavaScript في ملف واحد.
6. إذا كان المشروع لعبة HTML، اجعلها قابلة للتشغيل مباشرة في المتصفح.
7. اجعل التصميم مناسبًا للهاتف إذا لم يحدد المستخدم غير ذلك.
8. استخدم JavaScript عاديًا بدون React أو Vue أو Angular إذا لم يطلب المستخدم مكتبة معينة.
9. استخدم code fences المناسبة.
10. بعد الكود، اشرح طريقة التشغيل باختصار.
11. إذا كان الكود طويلًا، قلّل الشرح بدل حذف أجزاء من الكود.
12. لا تضع شرحًا طويلًا داخل كتلة الكود.
13. راجع الأقواس والوسوم والدوال قبل إنهاء الإجابة.
14. عند إنشاء لعبة، تأكد من وجود نقطة بداية واضحة للعبة.
15. أضف التحكم باللمس على الهاتف عندما يكون مناسبًا.
16. إذا طلب المستخدم تعديل كود سابق، حافظ على الأجزاء التي لا تحتاج إلى تغيير.
17. إذا كان المستخدم يشير إلى "الكود السابق"، استخدم سياق المحادثة السابقة لفهم الكود المقصود.

الأولوية:
الكود الكامل والصحيح أهم من الشرح الطويل.
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
- طرح أسئلة قصيرة للتأكد من الفهم عند الحاجة.
- استخدام العربية الواضحة عندما يكون السؤال بالعربية.

عند شرح درس دراسي:
1. ابدأ بتعريف بسيط.
2. اشرح القاعدة.
3. أعط أمثلة صحيحة.
4. وضح الأخطاء الشائعة.
5. أعط تمرينًا قصيرًا.
6. إذا أجاب المستخدم، صحح إجابته وفسر الخطأ.
7. لا تنتقل لموضوع جديد إذا كان المستخدم ما زال يسأل عن الموضوع الحالي.

إذا كان الموضوع صعبًا:
ابدأ بالفكرة الأساسية ثم انتقل إلى التفاصيل.

حافظ على سياق الدرس والمحادثة السابقة.
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

إذا طلب تعديل نص سابق:
اعتمد على النص الموجود في سياق المحادثة.
"""
}


# =========================================================
# Helpers
# =========================================================

def clean_text(value, default=""):
    """
    تحويل أي قيمة إلى نص آمن.
    """
    if value is None:
        return default

    return str(value).strip()


def get_mode_prompt(mode):
    """
    إرجاع Prompt مناسب للوضع.
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


def normalize_history(history):
    """
    تنظيف سجل المحادثة القادم من app.js.

    الشكل المتوقع:

    [
        {
            "type": "user",
            "text": "مرحبا"
        },
        {
            "type": "ai",
            "text": "مرحبا بك"
        }
    ]
    """

    if not isinstance(history, list):
        return []

    messages = []

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

            messages.append({
                "role": "user",
                "content": text
            })

        elif message_type == "ai":

            messages.append({
                "role": "assistant",
                "content": text
            })

    return messages


def detect_code_request(message):
    """
    اكتشاف طلبات البرمجة والكود.
    """

    keywords = [
        "اكتب كود",
        "أنشئ كود",
        "اصنع كود",
        "اكتب لي كود",
        "أنشئ لعبة",
        "اصنع لعبة",
        "لعبة html",
        "html",
        "css",
        "javascript",
        "java script",
        "python",
        "flask",
        "برمج",
        "برمجة",
        "كود كامل",
        "ملف html",
        "ملف واحد",
        "صفحة ويب",
        "موقع",
        "تطبيق ويب",
        "canvas"
    ]

    text = message.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def build_messages(
    system_prompt,
    history,
    current_message
):
    """
    إنشاء messages المتوافقة مع Chat Completion.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    cleaned_history = normalize_history(
        history
    )

    # نأخذ آخر جزء من المحادثة
    if cleaned_history:

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


# =========================================================
# Main Page
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

        "version": "4.3",

        "max_tokens": MAX_TOKENS,

        "max_history": MAX_HISTORY_MESSAGES

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
        data.get("mode"),
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
    # Limit input
    # -----------------------------------------------------

    if len(message) > 30000:

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
    # Extra instructions for code
    # -----------------------------------------------------

    if detect_code_request(
        message
    ):

        system_prompt += """

هذه الرسالة مرتبطة بالبرمجة أو إنشاء مشروع.

قبل إنهاء الإجابة:

- تأكد من أن الكود غير مقطوع.
- أغلق جميع HTML tags.
- أغلق جميع الأقواس { }.
- أغلق جميع الأقواس ( ).
- أغلق جميع الأقواس المربعة [ ].
- أكمل جميع الدوال.
- لا تتوقف في منتصف JavaScript.
- إذا كان المطلوب ملفًا واحدًا، أعطِ ملفًا واحدًا كاملًا.
- لا تستبدل أجزاء الكود بعبارة "...".
- اجعل الكود قابلًا للنسخ والتشغيل.
- إذا كان المشروع لعبة، تأكد من أن اللعبة تحتوي على بداية واضحة.
"""


    # -----------------------------------------------------
    # Build conversation
    # -----------------------------------------------------

    messages = build_messages(
        system_prompt,
        history,
        message
    )


    # -----------------------------------------------------
    # Request to Hugging Face
    # -----------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        # -------------------------------------------------
        # Extract response
        # -------------------------------------------------

        reply = extract_reply(
            response
        )


        # -------------------------------------------------
        # Empty response
        # -------------------------------------------------

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

            "version": "4.3"

        })


    # -----------------------------------------------------
    # Errors
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
# Error Handlers
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "ok": False,

        "error":
            "المسار غير موجود."

    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "ok": False,

        "error":
            "طريقة الطلب غير مسموحة."

    }), 405


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
# Local Development
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
