import os
import re
import time
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError


# =========================================================
# NORYN AI v8
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

# الحد الأقصى لعدد الأحرف في تاريخ المحادثة المرسل للنموذج
# (حماية من إرسال محادثات ضخمة جدًا للنموذج)
MAX_HISTORY_CHARS = int(
    os.environ.get("HF_MAX_HISTORY_CHARS", "24000")
)

# مهلة الطلب لـ Hugging Face (بالثواني) - اختياري
HF_TIMEOUT = int(
    os.environ.get("HF_TIMEOUT", "120")
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

MAX_HISTORY_CHARS = max(
    2000,
    min(MAX_HISTORY_CHARS, 100000)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN,
    timeout=HF_TIMEOUT
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

قواعد سياق المحادثة:

- سجل المحادثة (history) يمثل الرسائل السابقة فعليًا بين المستخدم وبينك.
- إذا كانت رسالة المستخدم الحالية قصيرة أو غامضة (مثل "وأيها أكبر؟" أو "أضف نظام نقاط")
  فاعتبرها امتدادًا مباشرًا لآخر موضوع أو مشروع تمت مناقشته في history، وليست سؤالًا مستقلًا.
- إذا طلب المستخدم تعديلًا على كود أو مشروع سابق، ابنِ على الكود الذي أعطيته سابقًا
  في المحادثة بدل البدء من الصفر، إلا إذا طلب صراحة نسخة جديدة.

قواعد الصدق:

- لا تدّع أنك نفذت أو شغّلت أو اختبرت كودًا فعليًا، لأنه ليس لديك بيئة تنفيذ حقيقية.
- لا تخترع نتائج تنفيذ أو مخرجات وهمية لأي كود.
- إذا لم تكن متأكدًا من معلومة، كن صريحًا بشأن ذلك.

اللغة:

إذا كان المستخدم يتحدث بالعربية فأجب بالعربية.
إذا طلب الإنجليزية فأجب بالإنجليزية.
إذا طلب لغة معينة فاستخدمها.
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

عندما يكون السؤال متابعة لسؤال سابق في history:
- اربط إجابتك بالموضوع السابق مباشرة دون إعادة شرح كل شيء من البداية.

لا تجعل الإجابات طويلة بلا حاجة.
"""


# =========================================================
# Programming Mode
# =========================================================

PROGRAMMER_PROMPT = BASE_IDENTITY + """

أنت الآن NORYN AI Programmer Engine.

أنت مبرمج ومهندس برمجيات ومراجع أكواد (Code Reviewer) محترف.

مجالات تخصصك:

HTML5, CSS3, JavaScript (Vanilla + Canvas + Games)
Python, Flask, REST APIs, JSON
Web Apps, Mobile-first UI
Debugging, Code Review, Refactoring
Software architecture, Performance, Security basics


== عند إنشاء كود جديد ==

1. افهم المطلوب جيدًا أولًا.
2. أنشئ كودًا كاملًا وقابلًا للتشغيل مباشرة.
3. لا تختصر أجزاء مهمة، ولا تستخدم "..." أو "// باقي الكود" بدل كود حقيقي.
4. أغلق كل الأقواس، الدوال، و HTML tags.
5. تأكد من صحة JavaScript وPython syntax قبل إعطاء الإجابة.
6. إذا طلب المستخدم ملفًا واحدًا:
   ضع HTML + CSS + JavaScript في ملف واحد.
7. إذا طلب مشروعًا متعدد الملفات:
   اكتب اسم كل ملف بوضوح مثل:
   FILE: filename.ext
   ثم أعطِ محتوى الملف كاملًا تحته.
8. اجعل المشاريع Mobile First ما لم يحدد المستخدم غير ذلك.
9. استخدم Vanilla JavaScript ما لم يطلب مكتبة أخرى، ولا تستخدم React/Vue/Angular من تلقاء نفسك.
10. الشرح بعد الكود يكون مختصرًا: طريقة التشغيل + أهم ما تغيّر.


== عند تعديل مشروع سابق تمت مناقشته في history ==

- هذا الطلب هو تعديل، وليس مشروعًا جديدًا.
- حافظ على: بنية الملفات، أسماء المتغيرات والدوال المهمة، API endpoints، الميزات العاملة.
- أضف فقط ما طلبه المستخدم (مثل: نظام نقاط، مؤثرات صوتية، تحسين تصميم...).
- أعد الكود كاملًا بعد التعديل، وليس فقط الجزء المتغير، إلا إذا طلب المستخدم صراحة مقتطفًا فقط.


== عند تصحيح كود (Debug) ==

1. حدد المشكلة بدقة.
2. اشرح سبب الخطأ بإيجاز.
3. أعطِ النسخة المصححة كاملة.
4. لا تحذف ميزات تعمل أصلًا إلا إذا كان ذلك ضروريًا لحل المشكلة.


== عند شرح كود (Explain) ==

- اشرح ماذا يفعل الكود بشكل عام أولًا.
- ثم اشرح الأجزاء المهمة أو المعقدة.
- تجنب إعادة كتابة الكود سطرًا بسطر ما لم يُطلب ذلك تحديدًا.


== عند تحسين كود (Refactor / Optimize) ==

- حافظ على نفس السلوك الوظيفي للكود ما لم يُطلب تغييره.
- وضّح ما الذي تحسّن ولماذا (أداء، قراءة، بنية...).
- أعطِ الكود الكامل بعد التحسين.


== عند إنشاء لعبة ==

تأكد من وجود:
- نقطة بداية واضحة.
- حالة للعبة (state).
- تحكم واضح (لوحة مفاتيح أو لمس).
- Game Over عند الحاجة.
- إعادة تشغيل.
- دعم الهاتف عندما يكون مناسبًا.


الأولوية دائمًا: الكود الكامل > صحة الكود > سهولة التشغيل > الشرح.
"""


# =========================================================
# Learning Mode
# =========================================================

LEARN_PROMPT = BASE_IDENTITY + """

أنت الآن مدرس ذكي وصبور.

عند شرح موضوع جديد استخدم هذا الترتيب:

- تعريف مبسط.
- الفكرة الأساسية.
- مثال واقعي أو عملي.
- كيفية التطبيق.
- سؤال قصير للتأكد من الفهم (عند الحاجة).

إذا كان سؤال المستخدم متابعة لموضوع سابق في history (مثل "ما أنواعها؟" بعد شرح موضوع):
- تابع نفس الموضوع مباشرة دون سؤال المستخدم "أي موضوع تقصد؟".

إذا أخطأ الطالب في إجابة:
- لا تسخر منه ولا تكن قاسيًا.
- صحح الخطأ بلطف واشرح السبب بوضوح.

إذا طلب درسًا كاملًا:
- نظّم الدرس بعناوين واضحة ومراحل متسلسلة.

إذا طلب اختبارًا أو تمارين:
- أنشئ أسئلة مناسبة لمستوى الموضوع.
- بعد إجابة المستخدم، صحح الإجابات واشرح الصواب والخطأ.

تذكر موضوع الدرس الحالي طوال المحادثة واستخدمه لربط الأسئلة التالية.
"""


# =========================================================
# Writing Mode
# =========================================================

WRITE_PROMPT = BASE_IDENTITY + """

أنت الآن مساعد كتابة محترف.

ساعد في:

- القصص والمقالات.
- توليد الأفكار.
- التلخيص وإعادة الصياغة.
- الرسائل والمحتوى التعليمي.
- الوصف الإبداعي.

إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة دون مقدمات طويلة.

إذا كان الطلب تعديلًا على نص سابق في history (مثل "اجعله أقصر" أو "غيّر الأسلوب"):
- عدّل النص السابق نفسه بدل كتابة نص جديد مختلف تمامًا.

حافظ على الأسلوب والنبرة التي طلبها المستخدم.
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
# Request Type Detection
# =========================================================
#
# طبقة اكتشاف نوع الطلب: عام / برمجة / تعلم / كتابة
# + نوع فرعي عند البرمجة: إنشاء / تصحيح / شرح / تحسين / مشروع كبير
#

DEBUG_KEYWORDS = [
    "صحح", "اصلح", "إصلاح", "debug", "fix", "error", "خطأ",
    "لا يعمل", "مايعملش", "not working", "crash", "traceback",
    "exception", "bug"
]

EXPLAIN_KEYWORDS = [
    "اشرح", "وضح", "explain", "شرح", "ماذا يفعل", "كيف يعمل",
    "what does this do", "how does this work"
]

IMPROVE_KEYWORDS = [
    "حسّن", "حسن", "طوّر", "طور", "refactor", "optimize", "تحسين",
    "أعد هيكلة", "clean up", "improve"
]

PROGRAMMING_KEYWORDS = [
    "كود", "برمج", "برمجة", "برنامج", "مشروع", "لعبة",
    "html", "css", "javascript", "js", "python", "flask",
    "api", "json", "sql", "debug", "debugging", "خطأ",
    "error", "تصحيح", "صحح", "اصلح", "إصلاح", "website",
    "web app", "function", "class", "code", "coding"
]

PROJECT_KEYWORDS = [
    "مشروع كامل", "تطبيق كامل", "موقع كامل", "لعبة كاملة",
    "ابني لي", "أنشئ لي مشروع", "build a project", "full project",
    "complete project", "full website", "complete website",
    "complete app"
]


def _contains_any(text, keywords):
    return any(keyword.lower() in text for keyword in keywords)


def is_programming_request(message):
    text = message.lower()
    return _contains_any(text, PROGRAMMING_KEYWORDS)


def is_large_project(message):
    text = message.lower()
    return _contains_any(text, PROJECT_KEYWORDS)


def is_debug_request(message):
    text = message.lower()
    return _contains_any(text, DEBUG_KEYWORDS)


def is_explain_request(message):
    text = message.lower()
    return _contains_any(text, EXPLAIN_KEYWORDS)


def is_improve_request(message):
    text = message.lower()
    return _contains_any(text, IMPROVE_KEYWORDS)


def detect_request_type(message, mode):
    """
    يحدد نوع الطلب لأغراض الـ instructions الداخلية فقط.
    لا يُرسل للمستخدم، ولا يغيّر شكل استجابة API.
    """

    programming = is_programming_request(message)

    if not programming:
        return mode  # general / learn / write كما هي

    if is_large_project(message):
        return "code_project"

    if is_debug_request(message):
        return "code_debug"

    if is_explain_request(message):
        return "code_explain"

    if is_improve_request(message):
        return "code_improve"

    return "code_create"


# =========================================================
# Build Programming Instructions
# =========================================================

def build_programming_instruction(message, mode, request_type):
    """
    إضافة تعليمات ذكية إضافية حسب نوع الطلب.
    """

    if not is_programming_request(message):
        return ""

    instruction = """

هذه رسالة برمجية. نفّذ مراجعة داخلية قبل إرسال الإجابة (لا تعرضها للمستخدم):

[1] هل فهمت المطلوب بدقة؟
[2] هل الطلب تعديل على كود/مشروع سابق في history، أم طلب جديد؟
[3] هل الكود كامل بلا أجزاء ناقصة أو "..."؟
[4] هل الأقواس و HTML tags مغلقة؟
[5] هل JavaScript/Python syntax صحيح؟
[6] هل أسماء العناصر والدوال متطابقة في كل مكان استُخدمت فيه؟
[7] هل الكود قابل للتشغيل مباشرة؟
"""

    if request_type == "code_project":
        instruction += """

هذا يبدو مشروعًا كبيرًا.
الأولوية القصوى: اكتمال المشروع.

إذا كان المطلوب ملفًا واحدًا: أعط ملفًا واحدًا كاملًا.
إذا كان المطلوب عدة ملفات: رتّب الإجابة بالشكل:
FILE: filename.ext
ثم الكود الكامل لهذا الملف.

لا تضع أجزاء وهمية، ولا تستخدم "..."، ولا تقل "أكمل بنفس الطريقة".
"""

    elif request_type == "code_debug":
        instruction += """

هذا طلب تصحيح كود (Debug).
اتبع الترتيب: حدد المشكلة -> اشرح السبب بإيجاز -> أعطِ الكود المصحح كاملًا.
لا تحذف ميزات تعمل أصلًا إلا إذا كان ذلك ضروريًا لحل المشكلة تحديدًا.
"""

    elif request_type == "code_explain":
        instruction += """

هذا طلب شرح كود (Explain).
ركّز على الشرح الواضح، ولا تعد كتابة الكود كاملًا إلا إذا طُلب ذلك صراحة.
"""

    elif request_type == "code_improve":
        instruction += """

هذا طلب تحسين/إعادة هيكلة كود (Refactor/Optimize).
حافظ على نفس السلوك الوظيفي ما لم يُطلب تغييره، ووضّح باختصار ما الذي تحسّن.
أعطِ الكود الكامل بعد التحسين.
"""

    else:
        instruction += """

إذا وُجد كود أو مشروع سابق مرتبط بهذا الطلب في history، ابنِ عليه بدل البدء من الصفر.
"""

    instruction += """

أنت في وضع البرمجة: كن عمليًا. إذا وُجد أكثر من حل، اختر الأبسط والأكثر استقرارًا
ما لم يطلب المستخدم شيئًا آخر تحديدًا.
"""

    return instruction


# =========================================================
# History Normalization
# =========================================================

def normalize_history(history, current_message):
    """
    تحويل history القادمة من JavaScript إلى رسائل يفهمها النموذج،
    مع:
    - تجاهل أي عنصر غير صالح.
    - عدم تكرار الرسالة الحالية إذا كانت آخر عنصر في history هو نفسها.
    - تقييد عدد الرسائل (MAX_HISTORY).
    - تقييد إجمالي عدد الأحرف (MAX_HISTORY_CHARS) بإسقاط الأقدم أولًا،
      مع الحفاظ دائمًا على أحدث الرسائل (أهم سياق للمتابعة).
    """

    if not isinstance(history, list):
        return []

    trimmed_by_count = history[-MAX_HISTORY:]

    parsed = []

    for item in trimmed_by_count:

        if not isinstance(item, dict):
            continue

        msg_type = clean_text(item.get("type")).lower()
        text = clean_text(item.get("text"))

        if not text:
            continue

        if msg_type == "user":
            parsed.append({"role": "user", "content": text})
        elif msg_type == "ai":
            parsed.append({"role": "assistant", "content": text})

    # منع تكرار الرسالة الحالية إذا كانت الواجهة أرسلتها مسبقًا ضمن history
    if (
        parsed
        and parsed[-1]["role"] == "user"
        and parsed[-1]["content"] == current_message
    ):
        parsed.pop()

    # تقييد إجمالي الأحرف: نحتفظ بأحدث الرسائل ونسقط الأقدم عند الحاجة
    total_chars = sum(len(item["content"]) for item in parsed)

    while parsed and total_chars > MAX_HISTORY_CHARS:
        removed = parsed.pop(0)
        total_chars -= len(removed["content"])

    return parsed


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

        choices = getattr(response, "choices", None)

        if not choices:
            return ""

        first = choices[0]

        message = getattr(first, "message", None)

        if message is None:
            return ""

        content = getattr(message, "content", None)

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
# Remove Accidental Extra Whitespace
# =========================================================

def clean_model_reply(reply):
    """
    تنظيف بسيط دون تغيير محتوى الكود.
    """

    if not reply:
        return ""

    reply = reply.strip()

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
    return render_template("index.html")


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
        "version": "8.0",
        "engine": "programmer",
        "max_tokens": MAX_TOKENS,
        "history_limit": MAX_HISTORY,
        "history_char_limit": MAX_HISTORY_CHARS
    })


# =========================================================
# API Information
# =========================================================

@app.route("/api")
def api_info():

    return jsonify({
        "ok": True,
        "name": "NORYN AI",
        "version": "8.0",
        "endpoints": [
            "/",
            "/health",
            "/api/chat"
        ]
    })


# =========================================================
# Chat API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    # -----------------------------------------------------
    # Read JSON
    # -----------------------------------------------------

    data = request.get_json(silent=True) or {}

    message = clean_text(data.get("message"))

    mode = safe_mode(data.get("mode", "general"))

    # ملاحظة: أي "system" يُرسل من العميل لا يُستخدم كـ system حقيقي،
    # فقط mode الخاص بالخادم هو الذي يحدد التعليمات.

    raw_history = data.get("history", [])


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
                "HF_TOKEN غير موجود في إعدادات Render."
            )
        }), 500


    # -----------------------------------------------------
    # Message size
    # -----------------------------------------------------

    if len(message) > MAX_MESSAGE_LENGTH:

        return jsonify({
            "ok": False,
            "error": (
                "الرسالة طويلة جدًا. حاول تقليل حجمها."
            )
        }), 413


    # -----------------------------------------------------
    # History
    # -----------------------------------------------------

    history = normalize_history(raw_history, message)


    # -----------------------------------------------------
    # Request type detection (داخلي فقط)
    # -----------------------------------------------------

    request_type = detect_request_type(message, mode)


    # -----------------------------------------------------
    # System Prompt
    # -----------------------------------------------------

    system_prompt = get_mode_prompt(mode)

    programming_instruction = build_programming_instruction(
        message,
        mode,
        request_type
    )

    if programming_instruction:
        system_prompt += "\n\n" + programming_instruction


    # -----------------------------------------------------
    # Build Messages
    # -----------------------------------------------------

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": message
    })


    # -----------------------------------------------------
    # Debug Logging (بدون أسرار)
    # -----------------------------------------------------

    print("\n========== NORYN REQUEST ==========", flush=True)
    print("Mode:", mode, flush=True)
    print("Request type:", request_type, flush=True)
    print("Model:", MODEL, flush=True)
    print("History messages sent:", len(history), flush=True)
    print("Message length:", len(message), flush=True)
    print("====================================\n", flush=True)


    # =====================================================
    # Call Hugging Face
    # =====================================================

    start_time = time.time()

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )

        elapsed = round(time.time() - start_time, 2)

        reply = extract_reply(response)

        if not reply:

            print(
                "NORYN ERROR: Empty response from model",
                "| elapsed:", elapsed,
                flush=True
            )

            return jsonify({
                "ok": False,
                "error": "النموذج لم يُرجع إجابة."
            }), 502

        reply = clean_model_reply(reply)

        print(
            "NORYN OK | elapsed:", elapsed,
            "s | reply length:", len(reply),
            flush=True
        )

        return jsonify({
            "ok": True,
            "reply": reply,
            "model": MODEL,
            "mode": mode,
            "version": "8.0",
            "programmer": is_programming_request(message)
        })


    # -----------------------------------------------------
    # Hugging Face specific errors (rate limit, model busy...)
    # -----------------------------------------------------

    except HfHubHTTPError as error:

        print(
            "\n===== NORYN HF HTTP ERROR =====",
            "\nError:", repr(error),
            "\n================================\n",
            flush=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "تعذر الاتصال بنموذج Hugging Face حاليًا "
                "(قد يكون النموذج مشغولًا أو هناك مشكلة في الاتصال). "
                "حاول مرة أخرى بعد قليل."
            )
        }), 502


    # -----------------------------------------------------
    # Any other unexpected error
    # -----------------------------------------------------

    except Exception as error:

        print("\n========== NORYN ERROR ==========", flush=True)
        print("Error:", repr(error), flush=True)
        traceback.print_exc()
        print("================================\n", flush=True)

        return jsonify({
            "ok": False,
            "error": (
                "تعذر الحصول على إجابة من NORYN AI الآن. "
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
        "error": "طريقة الطلب غير مسموحة."
    }), 405


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    print("NORYN INTERNAL ERROR:", repr(error), flush=True)

    return jsonify({
        "ok": False,
        "error": "حدث خطأ داخلي في الخادم."
    }), 500


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
