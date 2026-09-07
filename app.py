# =========================================================
# NORYN AI v7
# Search + Write
#
# Backend:
# Flask
# Hugging Face InferenceClient
# Brave Search API
#
# Features:
# - AI chat
# - Web search
# - Search + AI synthesis
# - Writing mode
# - Conversation memory
# - Arabic / English
# - Sources
# - Automatic search detection
# - Render compatible
# =========================================================

import os
import re
import traceback
from urllib.parse import quote

import requests

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from huggingface_hub import InferenceClient


# =========================================================
# APP
# =========================================================

app = Flask(__name__)


# =========================================================
# ENVIRONMENT
# =========================================================

HF_TOKEN = os.environ.get(
    "HF_TOKEN",
    ""
).strip()


HF_MODEL = os.environ.get(
    "HF_MODEL",
    "deepseek-ai/DeepSeek-V3-0324"
).strip()


BRAVE_API_KEY = os.environ.get(
    "BRAVE_SEARCH_API_KEY",
    ""
).strip()


# =========================================================
# AI SETTINGS
# =========================================================

MAX_TOKENS = int(
    os.environ.get(
        "HF_MAX_TOKENS",
        "4096"
    )
)


TEMPERATURE = float(
    os.environ.get(
        "HF_TEMPERATURE",
        "0.7"
    )
)


MAX_TOKENS = max(
    256,
    min(MAX_TOKENS, 8192)
)


TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)


# =========================================================
# SEARCH SETTINGS
# =========================================================

SEARCH_RESULTS_COUNT = int(
    os.environ.get(
        "SEARCH_RESULTS_COUNT",
        "8"
    )
)


SEARCH_RESULTS_COUNT = max(
    1,
    min(SEARCH_RESULTS_COUNT, 20)
)


SEARCH_COUNTRY = os.environ.get(
    "SEARCH_COUNTRY",
    "TN"
).strip().upper()


SEARCH_LANG = os.environ.get(
    "SEARCH_LANG",
    "ar"
).strip().lower()


# =========================================================
# HTTP SETTINGS
# =========================================================

REQUEST_TIMEOUT = int(
    os.environ.get(
        "REQUEST_TIMEOUT",
        "20"
    )
)


# =========================================================
# HUGGING FACE CLIENT
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# PROMPTS
# =========================================================

WRITE_PROMPT = """
أنت NORYN AI، مساعد متخصص في الكتابة.

مهمتك مساعدة المستخدم في:

- كتابة القصص.
- المقالات.
- النصوص.
- إعادة الصياغة.
- التلخيص.
- الأفكار.
- الرسائل.
- المحتوى الإبداعي.
- كتابة النصوص التعليمية.
- تحسين الأسلوب واللغة.

القواعد:

1. إذا كتب المستخدم بالعربية فأجب بالعربية.
2. إذا كتب بالإنجليزية فأجب بالإنجليزية.
3. إذا طلب نصًا جاهزًا، قدم النص مباشرة.
4. لا تضف شرحًا غير ضروري.
5. اجعل النص منظمًا وواضحًا.
6. لا تدّعي أنك بحثت في الويب إذا لم يتم البحث.
"""


SEARCH_PROMPT = """
أنت NORYN AI، مساعد بحث وكتابة ذكي.

ستحصل أحيانًا على نتائج بحث حقيقية من الويب.

مهمتك:

1. فهم سؤال المستخدم.
2. تحليل نتائج البحث.
3. الاعتماد على المصادر المتاحة بدل اختراع معلومات.
4. تقديم إجابة واضحة ومنظمة.
5. إذا كانت المصادر متعارضة، وضّح ذلك.
6. إذا كانت المعلومات حديثة، اذكر أنها مبنية على نتائج البحث الحالية.
7. لا تخترع مصدرًا أو رابطًا.
8. لا تقل إنك فتحت صفحة أو قرأت مصدرًا إذا لم يتم تزويدك بمحتواه.
9. إذا كانت نتائج البحث غير كافية، قل ذلك بوضوح.
10. إذا كان السؤال بالعربية، أجب بالعربية.
11. إذا كان السؤال بالإنجليزية، أجب بالإنجليزية.

عند استخدام نتائج البحث، أضف في نهاية الإجابة قسمًا بعنوان:

المصادر

واكتب المصادر باستخدام أرقام [1] و[2] و[3] حسب المعلومات التي استندت إليها.
"""


GENERAL_PROMPT = """
أنت NORYN AI، مساعد ذكي للبحث والكتابة.

يمكنك:

- الإجابة عن الأسئلة.
- البحث في الويب عندما تكون المعلومات بحاجة إلى تحديث أو تحقق.
- مساعدة المستخدم في الكتابة.
- التلخيص.
- الشرح.
- تنظيم الأفكار.

القواعد:

1. أجب باللغة التي يستخدمها المستخدم.
2. كن واضحًا ومباشرًا.
3. لا تخترع معلومات.
4. لا تدّعي استخدام أدوات لم تستخدمها.
5. إذا كانت المعلومة حديثة أو قابلة للتغير، فمن الأفضل الاعتماد على البحث.
6. إذا أعطيتك نتائج بحث، استخدمها في الإجابة واذكر المصادر.
"""


# =========================================================
# SEARCH DETECTION
# =========================================================

SEARCH_KEYWORDS_AR = [
    "آخر",
    "اخر",
    "اليوم",
    "حاليًا",
    "حاليا",
    "الآن",
    "الان",
    "حديث",
    "حديثة",
    "أخبار",
    "اخبار",
    "متى",
    "موعد",
    "سعر",
    "أسعار",
    "اسعار",
    "نتائج",
    "ترتيب",
    "معلومات عن",
    "من هو",
    "ما هو",
    "ما هي",
    "أين",
    "اين",
    "كيف",
    "أفضل",
    "افضل",
    "مقارنة",
    "قارن",
    "ابحث",
    "بحث",
    "مصادر",
    "حقيقة",
    "هل صحيح",
    "آخر الأخبار",
    "هذا الأسبوع",
    "هذا الشهر"
]


SEARCH_KEYWORDS_EN = [
    "latest",
    "today",
    "current",
    "now",
    "recent",
    "news",
    "price",
    "prices",
    "results",
    "ranking",
    "who is",
    "what is",
    "where is",
    "when",
    "best",
    "compare",
    "comparison",
    "search",
    "look up",
    "sources",
    "fact check",
    "this week",
    "this month"
]


WRITE_KEYWORDS_AR = [
    "اكتب لي",
    "اكتب",
    "أنشئ لي نص",
    "أنشئ نص",
    "قصة",
    "مقال",
    "رسالة",
    "قصيدة",
    "إعادة صياغة",
    "لخص",
    "لخص لي",
    "تلخيص",
    "صياغة",
    "وصف"
]


WRITE_KEYWORDS_EN = [
    "write me",
    "write",
    "story",
    "article",
    "letter",
    "poem",
    "rewrite",
    "summarize",
    "summary",
    "description"
]


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    default=""
):
    """
    تحويل القيمة إلى نص آمن.
    """

    if value is None:
        return default

    return str(value).strip()


def normalize_text(text):
    """
    تبسيط النص لاكتشاف الكلمات.
    """

    text = clean_text(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def detect_language(text):
    """
    اكتشاف بسيط للغة المستخدم.
    """

    text = clean_text(text)

    arabic_chars = len(
        re.findall(
            r"[\u0600-\u06FF]",
            text
        )
    )

    latin_chars = len(
        re.findall(
            r"[A-Za-z]",
            text
        )
    )

    if arabic_chars >= latin_chars:
        return "ar"

    return "en"


def is_write_request(message):
    """
    معرفة هل الطلب متعلق بالكتابة.
    """

    text = normalize_text(message)

    for keyword in WRITE_KEYWORDS_AR:
        if keyword in text:
            return True

    for keyword in WRITE_KEYWORDS_EN:
        if keyword in text:
            return True

    return False


def is_search_request(
    message,
    mode="general"
):
    """
    تحديد هل يجب استخدام بحث الويب.
    """

    text = normalize_text(message)

    mode = clean_text(
        mode,
        "general"
    ).lower()

    # إذا اختار المستخدم البحث صراحة
    if mode == "search":
        return True

    # كلمات تدل على البحث
    for keyword in SEARCH_KEYWORDS_AR:
        if keyword in text:
            return True

    for keyword in SEARCH_KEYWORDS_EN:
        if keyword in text:
            return True

    # أسئلة تحتوي على مؤشرات زمنية
    time_patterns = [
        r"\b20\d{2}\b",
        r"\b2026\b",
        r"\b2025\b",
        r"\b2027\b"
    ]

    for pattern in time_patterns:
        if re.search(
            pattern,
            text
        ):
            return True

    return False


def get_base_prompt(
    mode,
    use_search=False
):
    """
    اختيار النظام المناسب.
    """

    mode = clean_text(
        mode,
        "general"
    ).lower()

    if mode == "write":
        return WRITE_PROMPT

    if use_search:
        return SEARCH_PROMPT

    return GENERAL_PROMPT


# =========================================================
# CONVERSATION HISTORY
# =========================================================

def clean_history(history):
    """
    تنظيف سجل المحادثة القادم من app.js.
    """

    if not isinstance(
        history,
        list
    ):
        return []

    cleaned = []

    for item in history:

        if not isinstance(
            item,
            dict
        ):
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

            cleaned.append({
                "role": "user",
                "content": text
            })

        elif msg_type == "ai":

            cleaned.append({
                "role": "assistant",
                "content": text
            })

    # لا نسمح بتاريخ ضخم جدًا
    return cleaned[-20:]


# =========================================================
# BRAVE SEARCH
# =========================================================

def brave_search(
    query,
    language="ar"
):
    """
    البحث في الويب باستخدام Brave Search API.
    """

    if not BRAVE_API_KEY:

        raise RuntimeError(
            "BRAVE_SEARCH_API_KEY غير موجود في إعدادات Render."
        )

    query = clean_text(query)

    if not query:
        return []

    # Brave يضع حدًا لطول الاستعلام.
    query = query[:400]

    search_language = (
        "ar"
        if language == "ar"
        else "en"
    )

    url = (
        "https://api.search.brave.com"
        "/res/v1/web/search"
    )

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token":
            BRAVE_API_KEY
    }

    params = {
        "q": query,
        "count": SEARCH_RESULTS_COUNT,
        "country": SEARCH_COUNTRY,
        "search_lang": search_language,
        "safesearch": "strict"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    results = []

    web_data = data.get(
        "web",
        {}
    )

    raw_results = web_data.get(
        "results",
        []
    )

    if not isinstance(
        raw_results,
        list
    ):
        return []

    for index, result in enumerate(
        raw_results,
        start=1
    ):

        if not isinstance(
            result,
            dict
        ):
            continue

        title = clean_text(
            result.get("title")
        )

        url_value = clean_text(
            result.get("url")
        )

        description = clean_text(
            result.get("description")
        )

        if not url_value:
            continue

        results.append({
            "id": index,
            "title": title,
            "url": url_value,
            "description": description
        })

    return results


# =========================================================
# SEARCH CONTEXT
# =========================================================

def build_search_context(
    results
):
    """
    تحويل نتائج البحث إلى سياق مناسب للنموذج.
    """

    if not results:
        return (
            "لم يتم العثور على نتائج ويب "
            "كافية."
        )

    parts = []

    for result in results:

        number = result["id"]
        title = result["title"]
        url = result["url"]
        description = result["description"]

        block = f"""
المصدر [{number}]
العنوان: {title}
الرابط: {url}
المقتطف: {description}
"""

        parts.append(
            block.strip()
        )

    return "\n\n".join(parts)


# =========================================================
# SOURCE FORMAT
# =========================================================

def clean_sources(
    results
):
    """
    تجهيز المصادر لإرسالها للواجهة.
    """

    sources = []

    for result in results:

        sources.append({
            "id": result["id"],
            "title": result["title"],
            "url": result["url"],
            "description":
                result["description"]
        })

    return sources


# =========================================================
# AI RESPONSE
# =========================================================

def extract_reply(response):
    """
    استخراج النص من Hugging Face.
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

        return str(
            content
        ).strip()

    except Exception:

        return ""


# =========================================================
# BUILD AI MESSAGES
# =========================================================

def build_messages(
    system_prompt,
    history,
    user_message,
    search_context=""
):
    """
    بناء رسائل النموذج.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # ذاكرة المحادثة
    for item in history:

        messages.append(item)

    # نتائج البحث
    if search_context:

        messages.append({
            "role": "system",
            "content": (
                "نتائج البحث الحالية من الويب:\n\n"
                + search_context
                + "\n\n"
                "استخدم هذه النتائج عند الحاجة، "
                "ولا تخترع مصادر."
            )
        })

    messages.append({
        "role": "user",
        "content": user_message
    })

    return messages


# =========================================================
# MAIN PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "ok": True,

        "service":
            "NORYN AI",

        "version":
            "7.0",

        "ai":
            bool(HF_TOKEN),

        "search":
            bool(BRAVE_API_KEY),

        "model":
            HF_MODEL,

        "features": [
            "search",
            "write",
            "conversation-memory",
            "sources"
        ],

        "max_tokens":
            MAX_TOKENS
    })


# =========================================================
# DIRECT SEARCH API
# =========================================================

@app.route(
    "/api/search",
    methods=["POST"]
)
def search_api():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        query = clean_text(
            data.get("query")
        )

        language = clean_text(
            data.get(
                "language",
                "ar"
            )
        ).lower()

        if not query:

            return jsonify({
                "ok": False,
                "error":
                    "اكتب عبارة البحث أولًا."
            }), 400

        if len(query) > 400:

            return jsonify({
                "ok": False,
                "error":
                    "عبارة البحث طويلة جدًا."
            }), 400

        results = brave_search(
            query,
            language
        )

        return jsonify({

            "ok": True,

            "query":
                query,

            "results":
                clean_sources(results),

            "count":
                len(results)

        })

    except Exception as error:

        print(
            "\n========== SEARCH ERROR ==========",
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
                "تعذر تنفيذ البحث الآن."

        }), 502


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    try:

        # -------------------------------------------------
        # Read JSON
        # -------------------------------------------------

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

        history = clean_history(
            data.get(
                "history",
                []
            )
        )

        # -------------------------------------------------
        # Validate
        # -------------------------------------------------

        if not message:

            return jsonify({

                "ok": False,

                "error":
                    "اكتب رسالة أولًا."

            }), 400

        if len(message) > 30000:

            return jsonify({

                "ok": False,

                "error":
                    "الرسالة طويلة جدًا."

            }), 413

        if not HF_TOKEN:

            return jsonify({

                "ok": False,

                "error":
                    "HF_TOKEN غير موجود في إعدادات Render."

            }), 500

        # -------------------------------------------------
        # Determine search
        # -------------------------------------------------

        language = detect_language(
            message
        )

        writing_request = (
            is_write_request(
                message
            )
        )

        should_search = (
            is_search_request(
                message,
                mode
            )
        )

        # وضع الكتابة لا يحتاج بحثًا
        if mode == "write":

            should_search = False

        # إذا كان الطلب كتابة واضحة
        if writing_request:

            should_search = False

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        search_results = []

        search_context = ""

        if should_search:

            if not BRAVE_API_KEY:

                return jsonify({

                    "ok": False,

                    "error":
                        "البحث غير مفعّل. "
                        "أضف BRAVE_SEARCH_API_KEY "
                        "في Render Environment."

                }), 503

            search_results = brave_search(
                message,
                language
            )

            search_context = (
                build_search_context(
                    search_results
                )
            )

        # -------------------------------------------------
        # Prompt
        # -------------------------------------------------

        system_prompt = get_base_prompt(
            mode,
            should_search
        )

        # -------------------------------------------------
        # Additional search instructions
        # -------------------------------------------------

        if should_search:

            system_prompt += """

هذه إجابة مبنية على بحث ويب.

مهم جدًا:

- لا تخترع معلومات غير موجودة في النتائج.
- استخدم أرقام المصادر [1] [2] [3] عند الاستناد إليها.
- في نهاية الإجابة ضع قسم "المصادر".
- في قسم المصادر اذكر فقط المصادر التي تم توفيرها لك.
- لا تغير روابط المصادر.
"""

        # -------------------------------------------------
        # Additional writing instructions
        # -------------------------------------------------

        if mode == "write":

            system_prompt += """

أنت الآن في وضع الكتابة.

أعطِ المستخدم النص المطلوب مباشرة.
لا تبحث في الويب إلا إذا طلب المستخدم البحث صراحة.
"""

        # -------------------------------------------------
        # Build messages
        # -------------------------------------------------

        messages = build_messages(

            system_prompt,

            history,

            message,

            search_context
        )

        # -------------------------------------------------
        # AI request
        # -------------------------------------------------

        response = client.chat.completions.create(

            model=HF_MODEL,

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

            return jsonify({

                "ok": False,

                "error":
                    "النموذج لم يُرجع إجابة."

            }), 502

        # -------------------------------------------------
        # Sources
        # -------------------------------------------------

        sources = clean_sources(
            search_results
        )

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return jsonify({

            "ok": True,

            "reply":
                reply,

            "mode":
                mode,

            "searched":
                should_search,

            "language":
                language,

            "model":
                HF_MODEL,

            "version":
                "7.0",

            "sources":
                sources

        })

    # =====================================================
    # ERROR
    # =====================================================

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
# ERROR HANDLERS
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
# LOCAL DEVELOPMENT / RENDER
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
