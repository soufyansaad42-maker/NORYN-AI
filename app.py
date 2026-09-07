```python
import os
import json
import ast
import operator
import traceback
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient


# =========================================================
# NORYN AI v7
# =========================================================
#
# Flask + Hugging Face InferenceClient
#
# Features:
# - Conversation memory
# - Smart context
# - General / Code / Learn / Write
# - Tool calling
# - Safe calculator
# - Current date/time tool
# - Better code generation
# - Arabic / English support
# - Automatic tool selection
# - Robust error handling
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
        "8192"
    )
)


TEMPERATURE = float(
    os.environ.get(
        "HF_TEMPERATURE",
        "0.7"
    )
)


MAX_HISTORY_MESSAGES = int(
    os.environ.get(
        "NORYN_MAX_HISTORY",
        "30"
    )
)


MAX_MESSAGE_LENGTH = int(
    os.environ.get(
        "NORYN_MAX_MESSAGE_LENGTH",
        "30000"
    )
)


MAX_TOOL_ROUNDS = int(
    os.environ.get(
        "NORYN_MAX_TOOL_ROUNDS",
        "4"
    )
)


# Safety limits
MAX_TOKENS = max(
    512,
    min(MAX_TOKENS, 16384)
)


TEMPERATURE = max(
    0.0,
    min(TEMPERATURE, 2.0)
)


MAX_HISTORY_MESSAGES = max(
    4,
    min(MAX_HISTORY_MESSAGES, 60)
)


MAX_TOOL_ROUNDS = max(
    1,
    min(MAX_TOOL_ROUNDS, 6)
)


# =========================================================
# Hugging Face
# =========================================================

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


# =========================================================
# NORYN PERSONALITY
# =========================================================

BASE_PERSONALITY = """
أنت NORYN AI، مساعد ذكاء اصطناعي ذكي ومتعدد الاستخدامات.

هدفك ليس مجرد الإجابة، بل فهم ما يريده المستخدم
وتقديم أفضل مساعدة ممكنة.

القواعد الأساسية:

1. افهم السؤال قبل الإجابة.
2. استخدم سياق المحادثة السابقة.
3. إذا كان السؤال تابعًا لسؤال سابق، اربطه به.
4. لا تخترع معلومات أو نتائج.
5. إذا كنت غير متأكد، قل ذلك بوضوح.
6. إذا كانت هناك أداة مناسبة ومطلوبة، استخدمها.
7. لا تقل إنك استخدمت أداة إذا لم تستخدمها فعليًا.
8. لا تدّع تنفيذ شيء لم تنفذه.
9. أجب باللغة التي يستخدمها المستخدم.
10. إذا طلب المستخدم لغة محددة، استخدمها.
11. اجعل الإجابة منظمة وسهلة القراءة.
12. لا تطل بلا فائدة.
13. إذا احتاج الموضوع شرحًا، استخدم العناوين والنقاط والأمثلة.
14. حافظ على شخصية NORYN الهادئة والمفيدة.
"""


# =========================================================
# MODES
# =========================================================

MODE_PROMPTS = {

    "general": """
أنت في الوضع العام.

ساعد المستخدم في:
- الأسئلة العامة
- العلوم
- المعرفة
- الأفكار
- التخطيط
- الدراسة
- التقنية
- الحياة اليومية

كن واضحًا ودقيقًا.
""",

    "code": """
أنت في وضع البرمجة.

أنت مطور محترف متخصص في:

HTML5
CSS3
JavaScript
Python
Flask
Canvas
Web Apps
الألعاب
واجهات المستخدم
تصحيح الأخطاء
تحسين الأداء

عند كتابة كود:

- أعطِ كودًا كاملًا قدر الإمكان.
- لا تستخدم ... بدل أجزاء الكود.
- لا تقطع الكود في المنتصف.
- أغلق جميع الأقواس والوسوم.
- أكمل جميع الدوال.
- راجع الكود قبل إرساله.
- إذا طلب المستخدم ملفًا واحدًا، اجعله ملفًا واحدًا.
- إذا لم يطلب إطار عمل، استخدم JavaScript عاديًا.
- اجعل التصميم Mobile First عندما يكون ذلك مناسبًا.
- بعد الكود، اشرح التشغيل باختصار.
- إذا طلب المستخدم إصلاح كود سابق، حافظ على الأجزاء التي تعمل.
""",

    "learn": """
أنت مدرس ذكي.

عند التعليم:

- ابدأ من الأساسيات.
- اشرح خطوة بخطوة.
- استخدم أمثلة بسيطة.
- لا تفترض أن المستخدم خبير.
- اسأل أسئلة قصيرة عند الحاجة.
- صحح إجابة الطالب.
- إذا طلب المستخدم اختبارًا، أنشئ اختبارًا مناسبًا.
- إذا أخطأ المستخدم، اشرح الخطأ ثم أعطه فرصة للمحاولة.
- اربط الأسئلة الجديدة بالدرس السابق.
""",

    "write": """
أنت مساعد متخصص في الكتابة.

ساعد في:

- القصص
- المقالات
- الرسائل
- الأفكار
- التلخيص
- إعادة الصياغة
- الوصف
- المحتوى الإبداعي

إذا طلب المستخدم نصًا جاهزًا، أعطه النص مباشرة.
"""
}


# =========================================================
# TOOL DEFINITIONS
# =========================================================

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "calculator",

            "description": (
                "احسب العمليات الحسابية بدقة. "
                "استخدم هذه الأداة عندما يحتاج السؤال "
                "إلى عملية حسابية أو نتيجة رياضية."
            ),

            "parameters": {
                "type": "object",

                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "عملية حسابية مثل "
                            "25 * 18 أو (100 / 4) + 7"
                        )
                    }
                },

                "required": [
                    "expression"
                ]
            }
        }
    },


    {
        "type": "function",
        "function": {
            "name": "current_datetime",

            "description": (
                "الحصول على التاريخ والوقت الحاليين "
                "من خادم NORYN."
            ),

            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

]


# =========================================================
# SAFE CALCULATOR
# =========================================================

ALLOWED_OPERATORS = {

    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,

}


def safe_calculate(expression):
    """
    آلة حاسبة آمنة نسبيًا باستخدام AST.

    لا تستخدم eval مباشرة.
    """

    expression = str(
        expression
    ).strip()


    if not expression:
        raise ValueError(
            "التعبير الحسابي فارغ."
        )


    if len(expression) > 200:
        raise ValueError(
            "التعبير الحسابي طويل جدًا."
        )


    # منع بعض الرموز غير المطلوبة
    forbidden = [
        "__",
        "import",
        "open",
        "exec",
        "eval",
        "lambda",
        ";"
    ]


    lower_expression = expression.lower()


    for word in forbidden:

        if word in lower_expression:
            raise ValueError(
                "التعبير يحتوي على رمز غير مسموح."
            )


    node = ast.parse(
        expression,
        mode="eval"
    )


    def evaluate(current):

        # Number
        if isinstance(
            current,
            ast.Constant
        ):

            if isinstance(
                current.value,
                (int, float)
            ):

                if abs(
                    current.value
                ) > 10**100:

                    raise ValueError(
                        "الرقم كبير جدًا."
                    )

                return current.value


            raise ValueError(
                "قيمة غير مسموحة."
            )


        # Binary operator
        if isinstance(
            current,
            ast.BinOp
        ):

            left = evaluate(
                current.left
            )

            right = evaluate(
                current.right
            )


            operation = ALLOWED_OPERATORS.get(
                type(current.op)
            )


            if operation is None:
                raise ValueError(
                    "عملية غير مسموحة."
                )


            result = operation(
                left,
                right
            )


            if isinstance(
                result,
                (int, float)
            ):

                if abs(result) > 10**100:
                    raise ValueError(
                        "النتيجة كبيرة جدًا."
                    )


            return result


        # Unary
        if isinstance(
            current,
            ast.UnaryOp
        ):

            operation = ALLOWED_OPERATORS.get(
                type(current.op)
            )


            if operation is None:
                raise ValueError(
                    "عملية غير مسموحة."
                )


            value = evaluate(
                current.operand
            )


            return operation(
                value
            )


        raise ValueError(
            "تعبير غير مسموح."
        )


    result = evaluate(
        node.body
    )


    if isinstance(
        result,
        float
    ):

        if result.is_integer():
            return int(result)


    return result


# =========================================================
# TOOL EXECUTION
# =========================================================

def execute_tool(
    name,
    arguments
):

    try:

        if name == "calculator":

            expression = arguments.get(
                "expression",
                ""
            )

            result = safe_calculate(
                expression
            )

            return {
                "ok": True,
                "tool": "calculator",
                "expression": expression,
                "result": result
            }


        if name == "current_datetime":

            now = datetime.now(
                timezone.utc
            )

            return {
                "ok": True,
                "tool": "current_datetime",
                "utc": now.isoformat()
            }


        return {
            "ok": False,
            "error": (
                "الأداة المطلوبة غير موجودة."
            )
        }


    except Exception as error:

        return {
            "ok": False,
            "error": str(error)
        }


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value,
    default=""
):

    if value is None:
        return default

    return str(
        value
    ).strip()


def get_mode_prompt(
    mode
):

    mode = clean_text(
        mode,
        "general"
    ).lower()


    return MODE_PROMPTS.get(
        mode,
        MODE_PROMPTS["general"]
    )


# =========================================================
# CODE DETECTION
# =========================================================

def looks_like_code_request(
    message
):

    keywords = [

        "اكتب كود",
        "أكتب كود",
        "اعطني كود",
        "أعطني كود",
        "أنشئ كود",
        "اصنع كود",
        "أنشئ لعبة",
        "اصنع لعبة",
        "لعبة html",
        "ملف html",
        "كود كامل",
        "برمج",
        "برمجة",

        "html",
        "css",
        "javascript",
        "python",
        "flask",

        "code",
        "coding",
        "javascript",
        "website",
        "web app"

    ]


    text = message.lower()


    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# =========================================================
# BUILD SYSTEM PROMPT
# =========================================================

def build_system_prompt(
    mode,
    message
):

    prompt = (
        BASE_PERSONALITY
        + "\n\n"
        + get_mode_prompt(mode)
    )


    if looks_like_code_request(
        message
    ):

        prompt += """

هذه الرسالة تبدو مرتبطة بالبرمجة.

قبل إنهاء الإجابة:

- راجع الكود.
- لا تقطعه.
- لا تستخدم "..." بدل أجزاء مطلوبة.
- أغلق جميع HTML tags.
- أغلق جميع الأقواس.
- أكمل جميع الدوال.
- تأكد من صحة JavaScript.
- إذا طلب المستخدم ملفًا واحدًا، أعطه ملفًا واحدًا كاملًا.
"""


    prompt += """

إذا احتاج السؤال إلى عملية حسابية:
استخدم أداة calculator بدل التخمين.

إذا احتاج السؤال إلى الوقت أو التاريخ الحالي:
استخدم أداة current_datetime.

لا تستخدم الأدوات بدون سبب.
"""


    return prompt


# =========================================================
# CONVERSATION HISTORY
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


    if not isinstance(
        history,
        list
    ):

        history = []


    cleaned = []


    for item in history:

        if not isinstance(
            item,
            dict
        ):
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


        elif message_type == "ai":

            cleaned.append({

                "role": "assistant",

                "content": text

            })


    cleaned = cleaned[
        -MAX_HISTORY_MESSAGES:
    ]


    messages.extend(
        cleaned
    )


    messages.append({

        "role": "user",

        "content": current_message

    })


    return messages


# =========================================================
# RESPONSE HELPERS
# =========================================================

def extract_message(
    response
):

    if not response:
        return None


    try:

        choices = getattr(
            response,
            "choices",
            None
        )


        if not choices:
            return None


        return choices[0].message


    except Exception:

        return None


def extract_content(
    message
):

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


def extract_tool_calls(
    message
):

    if message is None:
        return []


    tool_calls = getattr(
        message,
        "tool_calls",
        None
    )


    if not tool_calls:
        return []


    return tool_calls


# =========================================================
# CONVERT TOOL CALL
# =========================================================

def serialize_tool_call(
    tool_call
):

    function = getattr(
        tool_call,
        "function",
        None
    )


    if function is None:

        return None


    name = getattr(
        function,
        "name",
        ""
    )


    arguments = getattr(
        function,
        "arguments",
        "{}"
    )


    call_id = getattr(
        tool_call,
        "id",
        ""
    )


    call_type = getattr(
        tool_call,
        "type",
        "function"
    )


    return {

        "id": call_id,

        "type": call_type,

        "function": {

            "name": name,

            "arguments": arguments

        }

    }


# =========================================================
# CHAT WITH TOOLS
# =========================================================

def run_ai(
    messages
):

    current_messages = list(
        messages
    )


    for round_number in range(
        MAX_TOOL_ROUNDS
    ):

        response = client.chat.completions.create(

            model=MODEL,

            messages=current_messages,

            tools=TOOLS,

            tool_choice="auto",

            max_tokens=MAX_TOKENS,

            temperature=TEMPERATURE

        )


        assistant_message = extract_message(
            response
        )


        if assistant_message is None:

            raise RuntimeError(
                "النموذج لم يُرجع رسالة."
            )


        tool_calls = extract_tool_calls(
            assistant_message
        )


        # ---------------------------------------------
        # No tools
        # ---------------------------------------------

        if not tool_calls:

            content = extract_content(
                assistant_message
            )


            if not content:

                raise RuntimeError(
                    "النموذج أعاد إجابة فارغة."
                )


            return content


        # ---------------------------------------------
        # Serialize assistant tool calls
        # ---------------------------------------------

        serialized_calls = []


        for tool_call in tool_calls:

            serialized = serialize_tool_call(
                tool_call
            )


            if serialized:
                serialized_calls.append(
                    serialized
                )


        # ---------------------------------------------
        # Add assistant message
        # ---------------------------------------------

        current_messages.append({

            "role": "assistant",

            "content": extract_content(
                assistant_message
            ) or None,

            "tool_calls": serialized_calls

        })


        # ---------------------------------------------
        # Execute tools
        # ---------------------------------------------

        for tool_call in serialized_calls:

            function = tool_call.get(
                "function",
                {}
            )


            name = function.get(
                "name",
                ""
            )


            raw_arguments = function.get(
                "arguments",
                "{}"
            )


            try:

                arguments = json.loads(
                    raw_arguments
                )

            except Exception:

                arguments = {}


            result = execute_tool(
                name,
                arguments
            )


            current_messages.append({

                "role": "tool",

                "tool_call_id":
                    tool_call.get(
                        "id",
                        ""
                    ),

                "content":
                    json.dumps(
                        result,
                        ensure_ascii=False
                    )

            })


    raise RuntimeError(
        "تم تجاوز الحد الأقصى لاستدعاءات الأدوات."
    )


# =========================================================
# HOME
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
    "/health"
)
def health():

    return jsonify({

        "ok": True,

        "ai":
            bool(HF_TOKEN),

        "model":
            MODEL,

        "service":
            "NORYN AI",

        "version":
            "7",

        "max_tokens":
            MAX_TOKENS,

        "history_messages":
            MAX_HISTORY_MESSAGES,

        "tools": [

            "calculator",

            "current_datetime"

        ]

    })


# =========================================================
# CHAT
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
        data.get(
            "message"
        )
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
    # Validation
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
                "الرسالة طويلة جدًا."

        }), 413


    if not HF_TOKEN:

        return jsonify({

            "ok": False,

            "error":
                "HF_TOKEN غير موجود في Render."

        }), 500


    # -----------------------------------------------------
    # System prompt
    # -----------------------------------------------------

    system_prompt = build_system_prompt(

        mode,

        message

    )


    # -----------------------------------------------------
    # Conversation
    # -----------------------------------------------------

    messages = build_messages(

        system_prompt,

        history,

        message

    )


    # -----------------------------------------------------
    # AI
    # -----------------------------------------------------

    try:

        reply = run_ai(
            messages
        )


        return jsonify({

            "ok": True,

            "reply": reply,

            "model": MODEL,

            "mode": mode,

            "version": "7"

        })


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
# RUN
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
