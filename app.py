import os
import traceback

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v5
# =========================================================
# Backend:
# Flask + Hugging Face InferenceClient
#
# Features:
# - NORYN identity
# - Founder information
# - General / Code / Learn / Write modes
# - Conversation history
# - Long code generation
# - Arabic-first behavior
# - JSON API
# - Render compatible
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
    os.environ.get("HF_MAX_TOKENS", "4096")
)

TEMPERATURE = float(
    os.environ.get("HF_TEMPERATURE", "0.7")
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
# Hugging Face Client
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN IDENTITY
# =========================================================
#
# هذه المعلومات هي الهوية الرسمية للمساعد.
# لا نريد من النموذج اختراع معلومات مختلفة عن المشروع.
# =========================================================

NORYN_IDENTITY = """
هوية NORYN AI:

الاسم:
NORYN AI

أصل الاسم:
اسم NORYN مستوحى من اسم مؤسس المشروع "نورالدين".

المؤسس:
نورالدين.

طبيعة المشروع:
NORYN AI هو مشروع مساعد ذكاء اصطناعي يهدف إلى مساعدة المستخدم
في التعلم والبرمجة والكتابة والإبداع والإجابة عن الأسئلة.

الشعار:
NORYN AI — تعلّم. ابتكر. طوّر.

النسخة الحالية:
NORYN AI v5.

معلومات مهمة:
- لا تدّعِ أن NORYN هو أول مساعد ذكاء اصطناعي في العالم.
- لا تدّعِ أن اسم NORYN حصري عالميًا.
- لا تخترع معلومات عن المؤسس أو المشروع.
- إذا سُئلت عن سبب اسم NORYN، اذكر أنه مستوحى من اسم نورالدين.
- إذا سُئلت "من صنعك؟" أو "من هو مؤسسك؟"، اذكر أن المشروع أسسه وطوره نورالدين.
- لا تدّعِ أن نورالدين هو من صنع نموذج الذكاء الاصطناعي الأساسي نفسه إذا لم تكن هذه المعلومة صحيحة.
- ميّز بين مشروع NORYN AI وبين نموذج الذكاء الاصطناعي المستخدم خلفه.
- إذا لم تكن لديك معلومة مؤكدة عن تفاصيل تقنية أو تجارية للمشروع، قل إن هذه المعلومة غير متوفرة لديك بدل اختلاقها.
"""


# =========================================================
# MODE PROMPTS
# =========================================================

PROMPTS = {

    "general": """
أنت NORYN AI، مساعد ذكاء اصطناعي عام.

مهمتك:
- الإجابة عن الأسئلة العامة.
- مساعدة المستخدم في التعلم.
- تقديم الأفكار والاقتراحات.
- شرح المواضيع بطريقة واضحة.
- المساعدة في التخطيط والتنظيم.
- المساعدة في الكتابة.
- المساعدة في البرمجة عند الطلب.

القواعد:
- أجب بالعربية عندما يكتب المستخدم بالعربية.
- إذا كتب المستخدم بلغة أخرى، يمكنك الإجابة بلغته.
- كن واضحًا وطبيعيًا.
- لا تكن مطولًا بلا سبب.
- إذا كان السؤال يحتاج شرحًا، استخدم تنظيمًا واضحًا.
- لا تدّعِ أنك نفذت شيئًا لم تنفذه.
- لا تخترع المعلومات.
- إذا لم تكن متأكدًا من معلومة، وضّح ذلك.
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
الألعاب
Canvas
تصحيح الأخطاء
تحسين الأكواد
شرح الأكواد
تصميم المشاريع

عند طلب إنشاء كود:

1. افهم المطلوب جيدًا.
2. أعطِ كودًا كاملًا وقابلًا للتشغيل قدر الإمكان.
3. لا تقطع الكود في المنتصف.
4. لا تستخدم "..." بدل الأجزاء المطلوبة.
5. لا تقل "أكمل الكود هنا".
6. إذا طلب المستخدم ملف HTML واحدًا، ضع HTML وCSS وJavaScript في ملف واحد.
7. اجعل مشاريع HTML قابلة للتشغيل مباشرة في المتصفح.
8. اجعل التصميم مناسبًا للهاتف إذا لم يحدد المستخدم غير ذلك.
9. استخدم JavaScript عاديًا بدل React أو Vue أو Angular إذا لم يطلب المستخدم إطارًا معينًا.
10. راجع الأقواس والوسوم والدوال قبل إنهاء الكود.
11. عند إنشاء لعبة، تأكد من وجود نقطة بداية واضحة للعبة.
12. أضف التحكم باللمس عندما يكون ذلك مناسبًا للأجهزة المحمولة.
13. إذا طلب المستخدم كودًا كاملًا، اجعل الكود هو الأولوية على الشرح الطويل.
14. لا تضع شرحًا طويلًا داخل كتلة الكود.
15. بعد الكود، أعطِ طريقة التشغيل باختصار.

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
- تصحيح أخطاء المتعلم بطريقة محترمة وواضحة.

إذا كان الموضوع صعبًا:
ابدأ بالفكرة الأساسية، ثم انتقل إلى التفاصيل.

عندما يطلب المستخدم درسًا:
- أعطه درسًا منظمًا.
- ابدأ بمقدمة بسيطة.
- اشرح المفاهيم الأساسية.
- أعطِ أمثلة.
- اختم بخلاصة.
- ويمكنك إضافة تمرين قصير إذا كان مناسبًا.
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


def extract_reply(response):
    """
    استخراج النص من نتيجة Hugging Face.
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


# =========================================================
# Conversation History
# =========================================================

def build_history(history):
    """
    تحويل تاريخ المحادثة القادم من app.js
    إلى messages مناسبة للنموذج.
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

    # حماية من تاريخ ضخم جدًا
    return messages[-30:]


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

        "version": "5.0",

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
    # Limit message size
    # -----------------------------------------------------

    if len(message) > 30000:

        return jsonify({

            "ok": False,

            "error":
                "الرسالة طويلة جدًا. حاول تقليل حجمها."

        }), 413


    # -----------------------------------------------------
    # Build System Prompt
    # -----------------------------------------------------

    system_prompt = (

        NORYN_IDENTITY

        + "\n\n"

        + get_mode_prompt(mode)

    )


    # -----------------------------------------------------
    # Detect coding request
    # -----------------------------------------------------

    code_keywords = [

        "اكتب كود",

        "أنشئ كود",

        "اصنع لعبة",

        "أنشئ لعبة",

        "html",

        "css",

        "javascript",

        "python",

        "flask",

        "برمج",

        "كود كامل",

        "ملف html",

        "لعبة",

        "برنامج",

        "موقع"

    ]


    is_code_request = any(

        keyword.lower()
        in message.lower()

        for keyword
        in code_keywords

    )


    if is_code_request:

        system_prompt += """

هذه الرسالة مرتبطة بالبرمجة أو إنشاء مشروع.

قبل إنهاء الإجابة:

- تأكد من أن الكود غير مقطوع.
- أغلق جميع HTML tags.
- أغلق الأقواس { }.
- أغلق الأقواس ( ).
- أغلق الأقواس [ ].
- أكمل جميع الدوال.
- لا تتوقف في منتصف JavaScript.
- إذا كان المطلوب ملفًا واحدًا، أعطِ ملفًا واحدًا كاملًا.
- لا تختصر أجزاء مهمة من الكود.
- لا تستخدم "..." داخل الكود بدل الأجزاء المطلوبة.
"""


    # -----------------------------------------------------
    # Build conversation
    # -----------------------------------------------------

    conversation = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]


    # إضافة تاريخ المحادثة
    # قبل السؤال الحالي

    conversation.extend(
        build_history(history)
    )


    # -----------------------------------------------------
    # Current User Message
    # -----------------------------------------------------

    conversation.append({

        "role": "user",

        "content": message

    })


    # -----------------------------------------------------
    # Request to Hugging Face
    # -----------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=conversation,

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        # -------------------------------------------------
        # Extract response
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

            "version": "5.0"

        })


    # -----------------------------------------------------
    # Hugging Face / HTTP / Inference Errors
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
# Local Development / Render
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
