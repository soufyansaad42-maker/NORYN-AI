import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v7
# Flask + Hugging Face InferenceClient
#
# Features:
# - Conversation memory
# - Context-aware conversations
# - General / Code / Learn / Write modes
# - Better Arabic behavior
# - Better English behavior
# - Long-code support
# - Context limiting
# - Automatic code-request detection
# - Safe server-side system prompts
# - Detailed error handling
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


# الحد الأقصى للتوكنات الناتجة
try:
    MAX_TOKENS = int(
        os.environ.get("HF_MAX_TOKENS", "8192")
    )
except (TypeError, ValueError):
    MAX_TOKENS = 8192


# درجة الإبداع
try:
    TEMPERATURE = float(
        os.environ.get("HF_TEMPERATURE", "0.7")
    )
except (TypeError, ValueError):
    TEMPERATURE = 0.7


# عدد الأحرف الأقصى التي نرسلها من سجل المحادثة
try:
    MAX_HISTORY_CHARS = int(
        os.environ.get("HF_MAX_HISTORY_CHARS", "50000")
    )
except (TypeError, ValueError):
    MAX_HISTORY_CHARS = 50000


# عدد الرسائل الأخيرة التي يسمح بها السياق
try:
    MAX_HISTORY_MESSAGES = int(
        os.environ.get("HF_MAX_HISTORY_MESSAGES", "30")
    )
except (TypeError, ValueError):
    MAX_HISTORY_MESSAGES = 30


# حماية القيم
MAX_TOKENS = max(256, min(MAX_TOKENS, 16384))

TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)

MAX_HISTORY_CHARS = max(
    4000,
    min(MAX_HISTORY_CHARS, 120000)
)

MAX_HISTORY_MESSAGES = max(
    4,
    min(MAX_HISTORY_MESSAGES, 100)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN Personality
# =========================================================

BASE_PERSONALITY = """
أنت NORYN AI، مساعد ذكاء اصطناعي ذكي ومتعدد الاستخدامات.

أنت مساعد:
- واضح
- دقيق
- مفيد
- متفاعل
- منظم
- صبور
- قادر على متابعة سياق المحادثة

افهم السؤال الحالي بالاعتماد على الرسائل السابقة عندما تكون ذات صلة.

إذا قال المستخدم:
"اشرح الثانية"
أو:
"ماذا تقصد؟"
أو:
"أعدها"
أو:
"تابع"
أو:
"حولها إلى الإنجليزية"

فلا تتعامل مع العبارة كأنها سؤال مستقل؛ استخدم سياق المحادثة السابق لفهم المقصود.

لا تسأل المستخدم عن معلومات سبق أن ذكرها بوضوح في نفس المحادثة.

إذا كانت الرسالة مرتبطة بموضوع سابق، تابع الموضوع بدل البدء من الصفر.

إذا غيّر المستخدم اللغة، استجب باللغة التي طلبها.

إذا كتب المستخدم بالعربية، استخدم العربية الواضحة.

إذا طلب الإنجليزية، أجب بالإنجليزية.

إذا طلب لغة أخرى، حاول الإجابة بها إذا كنت قادرًا.

لا تدّعي تنفيذ شيء لم تنفذه.

لا تخترع نتائج أو معلومات غير معروفة.

إذا كانت المعلومة غير مؤكدة، وضح ذلك.

اجعل الإجابة مناسبة للسؤال:
- سؤال بسيط = إجابة بسيطة.
- سؤال تعليمي = شرح منظم.
- سؤال برمجي = حل عملي وكود واضح.
- طلب كتابة = نص جاهز.
- طلب تحليل = تحليل منظم.
"""


# =========================================================
# Mode Prompts
# =========================================================

PROMPTS = {

    "general": BASE_PERSONALITY + """

أنت الآن في الوضع العام.

ساعد المستخدم في:
- الأسئلة العامة
- العلوم
- التاريخ
- الجغرافيا
- التكنولوجيا
- الأفكار
- التخطيط
- المعلومات اليومية
- التعلم
- البرمجة عند الحاجة

حافظ على أسلوب طبيعي يشبه المحادثة مع مساعد ذكي.
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
Web Apps
Mobile-first
واجهات المستخدم
الألعاب
تصحيح الأخطاء
تحسين الأكواد
شرح الأكواد
تصميم المشاريع

عند إنشاء كود:

1. افهم المطلوب.
2. قدم كودًا كاملًا قدر الإمكان.
3. لا تقطع الكود.
4. لا تستخدم "..." بدل أجزاء من الكود.
5. لا تكتب "أكمل هنا".
6. أغلق جميع الأقواس.
7. أغلق جميع الدوال.
8. أغلق جميع HTML tags.
9. إذا طلب المستخدم ملف HTML واحدًا، ضع HTML وCSS وJavaScript في ملف واحد.
10. إذا طلب لعبة HTML، اجعلها قابلة للتشغيل مباشرة.
11. اجعل المشاريع مناسبة للهاتف إذا لم يحدد المستخدم غير ذلك.
12. استخدم JavaScript عاديًا ما لم يطلب المستخدم إطارًا معينًا.
13. لا تضف مكتبات خارجية دون حاجة.
14. ضع الكود داخل code fence مناسب.
15. بعد الكود اشرح طريقة التشغيل باختصار.
16. لا تجعل الشرح الطويل يستهلك مساحة الكود.
17. راجع الكود منطقيًا قبل إرساله.

الأولوية:

الكود الكامل والقابل للتشغيل
ثم
الشرح.
""",


    "learn": BASE_PERSONALITY + """

أنت الآن مدرس ذكي.

مهمتك ليست فقط إعطاء الإجابة، بل مساعدة الطالب على الفهم.

عند شرح درس:

1. ابدأ بالمفهوم الأساسي.
2. استخدم لغة بسيطة.
3. قسم الشرح إلى نقاط.
4. أعط أمثلة.
5. وضح الأخطاء الشائعة.
6. استخدم أسئلة قصيرة للتأكد من الفهم عند الحاجة.
7. إذا طلب المستخدم اختبارًا، أنشئ اختبارًا مناسبًا.
8. إذا أجاب المستخدم عن سؤال، صحح إجابته واشرح السبب.
9. إذا أخطأ، لا تكتف بقول "خطأ"، بل وضح أين الخطأ.
10. إذا طلب إعادة الشرح، غيّر طريقة الشرح بدل تكرار النص نفسه.

تعامل مع المستخدم كطالب يتعلم معك خطوة بخطوة.
""",


    "write": BASE_PERSONALITY + """

أنت الآن مساعد متخصص في الكتابة.

ساعد في:
- القصص
- المقالات
- الأفكار
- التلخيص
- إعادة الصياغة
- الرسائل
- الوصف
- المحتوى الإبداعي
- العناوين
- التخطيط للكتب

إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة.

إذا طلب تحسين نص، حافظ على المعنى الأصلي وحسّن الأسلوب.

إذا طلب قصة، اجعلها مترابطة ومنظمة.
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
    الحصول على Prompt الخاص بالوضع.
    """
    mode = clean_text(
        mode,
        "general"
    ).lower()

    return PROMPTS.get(
        mode,
        PROMPTS["general"]
    )


# =========================================================
# Code Detection
# =========================================================

CODE_KEYWORDS = [

    "اكتب كود",
    "أنشئ كود",
    "اعطني كود",
    "أعطني كود",
    "اصنع كود",
    "أنشئ لعبة",
    "اصنع لعبة",
    "اكتب لعبة",
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
    "javascript code",
    "python code",
    "html code",
    "css code",
    "game",
    "code"
]


def is_code_request(message, mode):
    """
    تحديد ما إذا كان الطلب برمجيًا.
    """

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

CODE_REQUEST_PROMPT = """

هذه الرسالة تبدو مرتبطة بالبرمجة أو إنشاء مشروع.

قبل إرسال الإجابة:

- لا تقطع الكود.
- لا تستبدل أجزاء الكود بـ "...".
- أغلق جميع الأقواس.
- أغلق جميع الدوال.
- أغلق جميع HTML tags.
- أكمل JavaScript.
- تأكد من أسماء العناصر المستخدمة في JavaScript.
- تأكد من أن IDs الموجودة في JavaScript موجودة في HTML إذا كان الملف واحدًا.
- إذا كان المطلوب ملف HTML واحدًا، أرسل ملف HTML واحدًا كاملًا.
- اجعل المشروع قابلًا للتشغيل قدر الإمكان.
- لا تضع شرحًا طويلًا داخل الكود.
- اجعل الكود أولوية على الشرح.
"""


# =========================================================
# Build Conversation Messages
# =========================================================

def build_messages(
    system_prompt,
    history,
    current_message
):
    """
    تحويل history القادمة من app.js
    إلى صيغة Chat Completion:

    system
    user
    assistant
    user
    assistant
    ...
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]


    if not isinstance(history, list):
        history = []


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

        elif message_type in (
            "ai",
            "assistant"
        ):

            cleaned_history.append({
                "role": "assistant",
                "content": text
            })


    # -----------------------------------------------------
    # لا نسمح بإرسال عدد ضخم من الرسائل
    # -----------------------------------------------------

    cleaned_history = cleaned_history[
        -MAX_HISTORY_MESSAGES:
    ]


    # -----------------------------------------------------
    # التحكم في حجم النص
    # نحتفظ بالرسائل الأخيرة لأنها الأهم للسياق
    # -----------------------------------------------------

    selected = []

    total_chars = 0


    for item in reversed(cleaned_history):

        content = item["content"]

        size = len(content)

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


    # -----------------------------------------------------
    # إضافة الرسالة الحالية
    # -----------------------------------------------------

    messages.append({
        "role": "user",
        "content": current_message
    })


    return messages


# =========================================================
# Extract Reply
# =========================================================

def extract_reply(response):
    """
    استخراج النص من استجابة Hugging Face.
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

        "conversation_context": True,

        "max_tokens": MAX_TOKENS,

        "max_history_messages":
            MAX_HISTORY_MESSAGES,

        "max_history_chars":
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

    # =====================================================
    # Read JSON
    # =====================================================

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


    # =====================================================
    # Validate Mode
    # =====================================================

    if mode not in PROMPTS:

        mode = "general"


    # =====================================================
    # Validate Message
    # =====================================================

    if not message:

        return jsonify({

            "ok": False,

            "error":
                "اكتب رسالة أولًا."

        }), 400


    # =====================================================
    # Validate Token
    # =====================================================

    if not HF_TOKEN:

        return jsonify({

            "ok": False,

            "error":
                "HF_TOKEN غير موجود في إعدادات Render."

        }), 500


    # =====================================================
    # Input Limit
    # =====================================================

    if len(message) > 40000:

        return jsonify({

            "ok": False,

            "error":
                "الرسالة طويلة جدًا. حاول تقليل حجمها."

        }), 413


    # =====================================================
    # System Prompt
    # =====================================================

    system_prompt = get_mode_prompt(
        mode
    )


    # =====================================================
    # Code Mode
    # =====================================================

    if is_code_request(
        message,
        mode
    ):

        system_prompt += (
            CODE_REQUEST_PROMPT
        )


    # =====================================================
    # Build Conversation
    # =====================================================

    messages = build_messages(
        system_prompt=system_prompt,
        history=history,
        current_message=message
    )


    # =====================================================
    # Debug Information
    # =====================================================

    print(
        "\n========== NORYN REQUEST ==========",
        flush=True
    )

    print(
        "Mode:",
        mode,
        flush=True
    )

    print(
        "Model:",
        MODEL,
        flush=True
    )

    print(
        "History messages:",
        len(messages) - 2,
        flush=True
    )

    print(
        "Current message length:",
        len(message),
        flush=True
    )

    print(
        "===================================\n",
        flush=True
    )


    # =====================================================
    # Hugging Face Request
    # =====================================================

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        # =================================================
        # Extract Reply
        # =================================================

        reply = extract_reply(
            response
        )


        # =================================================
        # Empty Response
        # =================================================

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


        # =================================================
        # Success
        # =================================================

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


    # =====================================================
    # Hugging Face / Network Error
    # =====================================================

    except Exception as error:

        print(
            "\n========== NORYN AI ERROR ==========",
            flush=True
        )


        print(
            "Error:",
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
# Local / Render Start
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
