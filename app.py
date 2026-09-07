import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v7
# Search + Write
# Flask + Hugging Face
# =========================================================

app = Flask(__name__)


# =========================================================
# Environment
# =========================================================

HF_TOKEN = os.environ.get(
    "HF_TOKEN",
    ""
).strip()

MODEL = os.environ.get(
    "HF_MODEL",
    "deepseek-ai/DeepSeek-V3-0324"
).strip()

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

# حماية من القيم غير المناسبة
MAX_TOKENS = max(
    256,
    min(MAX_TOKENS, 8192)
)

TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)


# =========================================================
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN AI SYSTEM PROMPTS
# =========================================================

SEARCH_PROMPT = """
أنت NORYN AI، مساعد متخصص في البحث والمعرفة.

مهمتك الأساسية:
- الإجابة عن أسئلة المستخدم.
- شرح المعلومات بوضوح.
- مساعدة المستخدم على فهم المواضيع.
- ربط السؤال بسياق المحادثة السابقة.
- الإجابة بالعربية إذا كان المستخدم يكتب بالعربية.
- الإجابة باللغة التي يستخدمها المستخدم إذا طلب ذلك.

قواعد مهمة:
1. لا تخترع مصادر أو روابط أو حقائق غير متأكد منها.
2. إذا لم تكن متأكدًا من معلومة، قل ذلك بوضوح.
3. لا تدّعي أنك أجريت بحثًا مباشرًا على الإنترنت إذا لم يتم تزويدك بأداة بحث.
4. ميّز بين المعلومات المؤكدة والاحتمالات.
5. اجعل الإجابة منظمة وسهلة القراءة.
6. استخدم العناوين والقوائم عندما يكون ذلك مفيدًا.
7. إذا كان السؤال تعليميًا، اشرح الفكرة بطريقة بسيطة.
8. إذا كان السؤال يتطلب مقارنة، أنشئ مقارنة واضحة.
9. إذا طلب المستخدم اللغة الإنجليزية، أجب بالإنجليزية.
10. حافظ على سياق المحادثة السابقة.
"""


WRITE_PROMPT = """
أنت NORYN AI، مساعد متخصص في الكتابة والتحرير.

مهمتك:
- كتابة المقالات.
- كتابة القصص.
- كتابة المنشورات.
- كتابة الرسائل.
- إعادة الصياغة.
- التلخيص.
- تحسين النصوص.
- اقتراح العناوين.
- إنشاء الأفكار.
- تحويل الأفكار إلى نص منظم.

قواعد مهمة:
1. افهم المطلوب قبل الكتابة.
2. إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة.
3. لا تضف شرحًا طويلًا إذا لم يطلبه المستخدم.
4. حافظ على اللغة التي يطلبها المستخدم.
5. إذا كتب المستخدم بالعربية، اكتب بالعربية.
6. إذا طلب الإنجليزية، اكتب بالإنجليزية.
7. اجعل النص طبيعيًا ومنظمًا.
8. لا تكرر الجمل بلا سبب.
9. عند إعادة الصياغة، حافظ على المعنى الأصلي.
10. إذا طلب المستخدم أسلوبًا معينًا، التزم به.
"""


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


def get_system_prompt(mode):
    """
    اختيار شخصية NORYN حسب الوضع.
    """

    mode = clean_text(
        mode,
        "search"
    ).lower()

    if mode == "write":
        return WRITE_PROMPT

    return SEARCH_PROMPT


def normalize_history(history):
    """
    تحويل تاريخ المحادثة القادم من JavaScript
    إلى صيغة messages التي يفهمها النموذج.
    """

    if not isinstance(history, list):
        return []

    messages = []

    # نأخذ آخر 20 رسالة فقط
    history = history[-20:]

    for item in history:

        if not isinstance(item, dict):
            continue

        message_type = clean_text(
            item.get("type")
        )

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

        return str(
            content
        ).strip()

    except Exception:

        return ""


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
        "version": "7",
        "modes": [
            "search",
            "write"
        ],
        "max_tokens": MAX_TOKENS
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
        "search"
    ).lower()


    history = data.get(
        "history",
        []
    )


    # -----------------------------------------------------
    # Validate mode
    # -----------------------------------------------------

    if mode not in {
        "search",
        "write"
    }:

        mode = "search"


    # -----------------------------------------------------
    # Validate message
    # -----------------------------------------------------

    if not message:

        return jsonify({
            "ok": False,
            "error":
                "اكتب رسالتك أولًا."
        }), 400


    # -----------------------------------------------------
    # Validate HF token
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
                "الرسالة طويلة جدًا."
        }), 413


    # -----------------------------------------------------
    # System Prompt
    # -----------------------------------------------------

    system_prompt = get_system_prompt(
        mode
    )


    # -----------------------------------------------------
    # Normalize conversation
    # -----------------------------------------------------

    conversation =
        normalize_history(
            history
        )


    # -----------------------------------------------------
    # Prevent duplicate current message
    # -----------------------------------------------------

    if conversation:

        last = conversation[-1]

        if (
            last.get("role") == "user"
            and
            last.get("content") == message
        ):

            conversation = conversation[:-1]


    # -----------------------------------------------------
    # Build final messages
    # -----------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]


    messages.extend(
        conversation
    )


    messages.append({

        "role": "user",

        "content": message

    })


    # -----------------------------------------------------
    # Special instructions
    # -----------------------------------------------------

    if mode == "search":

        messages.append({

            "role": "system",

            "content": """
أجب عن السؤال الحالي اعتمادًا على
المعلومات التي تعرفها وسياق المحادثة.

إذا كان السؤال متابعة لسؤال سابق،
استخدم السياق السابق لفهم المقصود.

لا تدّعي إجراء بحث مباشر على الإنترنت
ما لم تكن لديك أداة بحث فعلية.
"""
        })


    elif mode == "write":

        messages.append({

            "role": "system",

            "content": """
ركز على تنفيذ طلب الكتابة الحالي.

إذا طلب المستخدم نصًا جاهزًا:
ابدأ بالنص مباشرة.

إذا طلب إعادة صياغة:
حافظ على المعنى.

إذا طلب قصة:
اجعلها مترابطة ولها بداية ووسط ونهاية.

إذا طلب مقالًا:
نظمه إلى مقدمة وفقرات وخاتمة
عندما يكون ذلك مناسبًا.
"""
        })


    # -----------------------------------------------------
    # Hugging Face Request
    # -----------------------------------------------------

    try:

        response = (
            client.chat.completions.create(

                model=MODEL,

                messages=messages,

                max_tokens=MAX_TOKENS,

                temperature=TEMPERATURE
            )
        )


        # -------------------------------------------------
        # Extract reply
        # -------------------------------------------------

        reply = extract_reply(
            response
        )


        if not reply:

            print(
                "NORYN ERROR: Empty response",
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

            "version": "7"

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
