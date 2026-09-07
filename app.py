```python
import os
import re
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v7
# Advanced Programmer + General AI Backend
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

MAX_TOKENS = int(
    os.environ.get("HF_MAX_TOKENS", "8192")
)

TEMPERATURE = float(
    os.environ.get("HF_TEMPERATURE", "0.65")
)

MAX_HISTORY = int(
    os.environ.get("HF_MAX_HISTORY", "24")
)

MAX_MESSAGE_LENGTH = int(
    os.environ.get("HF_MAX_MESSAGE_LENGTH", "50000")
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

MAX_HISTORY = max(
    4,
    min(MAX_HISTORY, 50)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN Identity
# =========================================================

BASE_IDENTITY = """
أنت NORYN AI، مساعد ذكاء اصطناعي متقدم.

أنت مساعد حقيقي متعدد الاستخدامات، ولست مجرد مولد نصوص.

قدراتك الأساسية:

- الإجابة عن الأسئلة.
- التعليم والشرح.
- البرمجة.
- تحليل الأكواد.
- تصحيح الأخطاء.
- إنشاء المشاريع.
- تطوير HTML/CSS/JavaScript.
- Python وFlask.
- إنشاء الألعاب.
- الكتابة.
- التلخيص.
- إعادة الصياغة.
- التفكير المنطقي.
- تحليل المشاكل.
- التخطيط للمشاريع.

تذكر سياق المحادثة الحالية واستخدمه عندما يكون مفيدًا.

إذا كان المستخدم يتحدث بالعربية فأجب بالعربية.
إذا طلب الإنجليزية فأجب بالإنجليزية.
إذا طلب لغة معينة فاستخدمها.

لا تدّع أنك نفذت شيئًا خارج المحادثة إذا لم تنفذه فعليًا.

إذا لم تكن متأكدًا من معلومة، كن صريحًا بشأن ذلك.
"""


# =========================================================
# General Mode
# =========================================================

GENERAL_PROMPT = BASE_IDENTITY + """

أنت الآن في الوضع العام.

أجب بشكل واضح ومباشر.

عندما يكون السؤال تعليميًا:
- اشرح الفكرة.
- أعط أمثلة.
- اختبر فهم المستخدم عند الحاجة.

عندما يكون السؤال يحتاج خطوات:
- رتّب الخطوات.
- لا تقفز إلى النتيجة فقط.

لا تجعل الإجابات طويلة بلا حاجة.
"""


# =========================================================
# Programming Mode
# =========================================================

PROGRAMMER_PROMPT = BASE_IDENTITY + """

أنت الآن NORYN AI Programmer Engine.

أنت مبرمج ومهندس برمجيات مساعد.

مجالاتك:

HTML5
CSS3
JavaScript
Python
Flask
REST APIs
JSON
Web Apps
Mobile-first UI
Canvas
Games
Debugging
Software architecture
Code optimization
Security basics
Performance
Project structure


عند طلب إنشاء كود:

1. افهم المطلوب.
2. أنشئ كودًا كاملًا قدر الإمكان.
3. لا تختصر أجزاء مهمة.
4. لا تستخدم:
   ...
   أو
   // باقي الكود
   بدل الكود الحقيقي.
5. أغلق جميع الأقواس.
6. أغلق جميع الدوال.
7. أغلق جميع HTML tags.
8. تأكد من صحة JavaScript.
9. إذا طلب المستخدم ملف HTML واحدًا:
   ضع HTML + CSS + JavaScript في ملف واحد.
10. إذا طلب مشروعًا متعدد الملفات:
   وضّح أسماء الملفات ثم أعط محتوى كل ملف كاملًا.
11. اجعل المشاريع Mobile First عندما لا يحدد المستخدم غير ذلك.
12. استخدم Vanilla JavaScript إذا لم يطلب مكتبة أخرى.
13. لا تستخدم React أو Vue أو Angular من تلقاء نفسك.
14. لا تضع الشرح الطويل داخل الكود.
15. بعد الكود أعط طريقة التشغيل باختصار.


عند تصحيح كود:

- حدد المشكلة.
- اشرح سببها.
- أعط النسخة المصححة.
- لا تحذف ميزات تعمل أصلًا إلا إذا كان ذلك ضروريًا.


عند تطوير مشروع موجود:

لا تبدأ من الصفر بدون سبب.

حافظ على:
- API endpoints الموجودة.
- أسماء الملفات.
- المتغيرات المهمة.
- الميزات الموجودة.

ثم أضف التحسين المطلوب.


عند إنشاء لعبة:

تأكد من وجود:
- نقطة بداية.
- حالة للعبة.
- تحكم واضح.
- Game Over عند الحاجة.
- إعادة تشغيل.
- دعم الهاتف عندما يكون مناسبًا.
- واجهة واضحة.


الأولوية:

الكود الكامل
ثم صحة الكود
ثم سهولة التشغيل
ثم الشرح.
"""


# =========================================================
# Learning Mode
# =========================================================

LEARN_PROMPT = BASE_IDENTITY + """

أنت الآن مدرس ذكي.

اشرح بطريقة تناسب المبتدئ.

استخدم:

- تعريف.
- فكرة أساسية.
- مثال.
- تطبيق.
- سؤال قصير عند الحاجة.

إذا أخطأ الطالب:
لا تسخر منه.

صحح الخطأ واشرح السبب.

إذا طلب درسًا كاملًا:
نظّم الدرس بعناوين واضحة.

إذا طلب اختبارًا:
أنشئ أسئلة مناسبة للموضوع ثم صحح الإجابات.
"""


# =========================================================
# Writing Mode
# =========================================================

WRITE_PROMPT = BASE_IDENTITY + """

أنت الآن مساعد كتابة.

ساعد في:

- القصص.
- المقالات.
- الأفكار.
- التلخيص.
- إعادة الصياغة.
- الرسائل.
- المحتوى التعليمي.
- الوصف.

إذا طلب المستخدم نصًا جاهزًا:
أعطه النص مباشرة.

حافظ على الأسلوب المطلوب.
"""


# =========================================================
# Modes
# =========================================================

PROMPTS = {
    "general": GENERAL_PROMPT,
    "code": PROGRAMMER_PROMPT,
    "learn": LEARN_PROMPT,
    "write": WRITE_PROMPT,
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


def safe_mode(mode):
    """
    التأكد من أن الوضع صالح.
    """
    mode = clean_text(
        mode,
        "general"
    ).lower()

    if mode not in PROMPTS:
        return "general"

    return mode


def get_mode_prompt(mode):
    """
    إرجاع System Prompt المناسب.
    """
    return PROMPTS.get(
        safe_mode(mode),
        PROMPTS["general"]
    )


# =========================================================
# Detect Programming Request
# =========================================================

PROGRAMMING_KEYWORDS = [
    "كود",
    "برمج",
    "برمجة",
    "برنامج",
    "مشروع",
    "لعبة",
    "html",
    "css",
    "javascript",
    "js",
    "python",
    "flask",
    "api",
    "json",
    "sql",
    "debug",
    "debugging",
    "خطأ",
    "error",
    "تصحيح",
    "صحح",
    "اصلح",
    "إصلاح",
    "website",
    "web app",
    "function",
    "class",
    "code",
    "coding"
]


def is_programming_request(message):
    """
    معرفة ما إذا كان الطلب برمجيًا.
    """

    text = message.lower()

    return any(
        keyword.lower() in text
        for keyword in PROGRAMMING_KEYWORDS
    )


# =========================================================
# Detect Large Project Request
# =========================================================

PROJECT_KEYWORDS = [
    "مشروع كامل",
    "تطبيق كامل",
    "موقع كامل",
    "لعبة كاملة",
    "ابني لي",
    "أنشئ لي مشروع",
    "build a project",
    "full project",
    "complete project",
    "full website",
    "complete website",
    "complete app"
]


def is_large_project(message):
    text = message.lower()

    return any(
        keyword.lower() in text
        for keyword in PROJECT_KEYWORDS
    )


# =========================================================
# Build Programming Instructions
# =========================================================

def build_programming_instruction(
    message,
    mode
):
    """
    إضافة تعليمات ذكية للطلبات البرمجية.
    """

    if not is_programming_request(message):
        return ""

    instruction = """

هذه رسالة برمجية.

نفّذ مراجعة داخلية قبل إرسال الإجابة.

CHECKLIST:

[1] هل فهمت المطلوب؟
[2] هل الكود كامل؟
[3] هل توجد أجزاء ناقصة؟
[4] هل الأقواس مغلقة؟
[5] هل HTML tags مغلقة؟
[6] هل JavaScript syntax منطقي؟
[7] هل أسماء العناصر متطابقة؟
[8] هل الأحداث مرتبطة بالعناصر الصحيحة؟
[9] هل API paths صحيحة؟
[10] هل الكود قابل للتشغيل؟

لا تعرض هذه القائمة للمستخدم.

استخدمها فقط للمراجعة الداخلية.
"""

    if is_large_project(message):

        instruction += """

هذا يبدو مشروعًا كبيرًا.

الأولوية هي الحفاظ على اكتمال المشروع.

إذا كان المطلوب ملفًا واحدًا:
أعط ملفًا واحدًا كاملًا.

إذا كان المطلوب عدة ملفات:
رتّب الإجابة هكذا:

FILE: filename.ext

ثم الكود الكامل.

لا تضع أجزاء وهمية.
لا تستخدم "...".
لا تقل "أكمل بنفس الطريقة".
"""

    if mode == "code":

        instruction += """

أنت في وضع البرمجة.

كن عمليًا جدًا.

إذا كان هناك أكثر من حل:
اختر الحل الأبسط والأكثر استقرارًا ما لم يطلب المستخدم شيئًا آخر.
"""

    return instruction


# =========================================================
# History Normalization
# =========================================================

def normalize_history(history):
    """
    تحويل history القادمة من JavaScript
    إلى رسائل يفهمها نموذج المحادثة.
    """

    if not isinstance(history, list):
        return []

    result = []

    for item in history[-MAX_HISTORY:]:

        if not isinstance(item, dict):
            continue

        msg_type = clean_text(
            item.get("type")
        ).lower()

        text = clean_text(
            item.get("text")
        )

        if not text:
            continue

        if msg_type == "user":

            result.append({
                "role": "user",
                "content": text
            })

        elif msg_type == "ai":

            result.append({
                "role": "assistant",
                "content": text
            })

    return result


# =========================================================
# Extract Reply
# =========================================================

def extract_reply(response):
    """
    استخراج إجابة النموذج.
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
            "NORYN extraction error:",
            repr(error),
            flush=True
        )

        return ""


# =========================================================
# Remove Accidental Duplicate Fences
# =========================================================

def clean_model_reply(reply):
    """
    تنظيف بسيط دون تغيير محتوى الكود.
    """

    if not reply:
        return ""

    reply = reply.strip()

    # إزالة مسافات زائدة جدًا
    reply = re.sub(
        r"\n{5,}",
        "\n\n\n",
        reply
    )

    return reply


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
        "version": "7.0",
        "engine": "programmer",
        "max_tokens": MAX_TOKENS,
        "history_limit": MAX_HISTORY
    })


# =========================================================
# API Information
# =========================================================

@app.route("/api")
def api_info():

    return jsonify({
        "ok": True,
        "name": "NORYN AI",
        "version": "7.0",
        "endpoints": [
            "/",
            "/health",
            "/api/chat"
        ]
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

    mode = safe_mode(
        data.get(
            "mode",
            "general"
        )
    )

    history = normalize_history(
        data.get(
            "history",
            []
        )
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
            "error": (
                "HF_TOKEN غير موجود "
                "في إعدادات Render."
            )
        }), 500


    # -----------------------------------------------------
    # Message size
    # -----------------------------------------------------

    if len(message) > MAX_MESSAGE_LENGTH:

        return jsonify({
            "ok": False,
            "error": (
                "الرسالة طويلة جدًا. "
                "حاول تقليل حجمها."
            )
        }), 413


    # -----------------------------------------------------
    # System Prompt
    # -----------------------------------------------------

    system_prompt = get_mode_prompt(
        mode
    )


    # -----------------------------------------------------
    # Client-provided system
    #
    # لا نثق به كـ system حقيقي.
    # نستخدم فقط mode الخاص بنا.
    # -----------------------------------------------------

    programming_instruction = (
        build_programming_instruction(
            message,
            mode
        )
    )


    system_prompt += (
        "\n\n"
        + programming_instruction
    )


    # -----------------------------------------------------
    # Build Messages
    # -----------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]


    # -----------------------------------------------------
    # Conversation Memory
    # -----------------------------------------------------

    messages.extend(
        history
    )


    # -----------------------------------------------------
    # Current User Message
    # -----------------------------------------------------

    messages.append({

        "role": "user",

        "content": message

    })


    # -----------------------------------------------------
    # Debug Information
    # -----------------------------------------------------

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
        len(history),
        flush=True
    )

    print(
        "Programming request:",
        is_programming_request(message),
        flush=True
    )

    print(
        "Large project:",
        is_large_project(message),
        flush=True
    )

    print(
        "===================================\n",
        flush=True
    )


    # =====================================================
    # Call Hugging Face
    # =====================================================

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        # -------------------------------------------------
        # Extract
        # -------------------------------------------------

        reply = extract_reply(
            response
        )


        # -------------------------------------------------
        # Empty response
        # -------------------------------------------------

        if not reply:

            print(
                "NORYN ERROR: Empty response",
                flush=True
            )

            return jsonify({
                "ok": False,
                "error": (
                    "النموذج لم يُرجع إجابة."
                )
            }), 502


        # -------------------------------------------------
        # Clean
        # -------------------------------------------------

        reply = clean_model_reply(
            reply
        )


        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return jsonify({

            "ok": True,

            "reply": reply,

            "model": MODEL,

            "mode": mode,

            "version": "7.0",

            "programmer": (
                is_programming_request(
                    message
                )
            )

        })


    # =====================================================
    # Error
    # =====================================================

    except Exception as error:

        print(
            "\n========== NORYN ERROR ==========",
            flush=True
        )

        print(
            "Error:",
            repr(error),
            flush=True
        )

        traceback.print_exc()

        print(
            "================================\n",
            flush=True
        )


        return jsonify({

            "ok": False,

            "error": (
                "تعذر الحصول على إجابة "
                "من NORYN AI الآن. "
                "تحقق من Render Logs."
            )

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

        "error": (
            "طريقة الطلب غير مسموحة."
        )

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

        "error": (
            "حدث خطأ داخلي في الخادم."
        )

    }), 500


# =========================================================
# Run
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
