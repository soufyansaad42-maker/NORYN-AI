const chat = document.getElementById("chat");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const themeBtn = document.getElementById("themeBtn");
const welcome = document.getElementById("welcome");

// رابط NORYN AI Backend على Render
const API_URL = "https://noryn-ai-backend.onrender.com/api/chat";

// =========================
// إضافة رسالة
// =========================

function addMessage(text, type = "ai") {
  const message = document.createElement("div");
  message.className = `message ${type}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  message.appendChild(bubble);
  chat.appendChild(message);

  chat.scrollTop = chat.scrollHeight;

  return message;
}

// =========================
// إرسال الرسالة
// =========================

async function sendMessage(text = null) {
  const messageText = (text ?? input.value).trim();

  if (!messageText) return;

  if (welcome) {
    welcome.remove();
  }

  // عرض رسالة المستخدم
  addMessage(messageText, "user");

  input.value = "";

  // تعطيل زر الإرسال أثناء الطلب
  sendBtn.disabled = true;

  // رسالة مؤقتة
  const loading = addMessage("NORYN AI يفكر... ⏳", "ai");

  try {
    const response = await fetch(API_URL, {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        message: messageText
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || `HTTP ${response.status}`
      );
    }

    // إزالة رسالة الانتظار
    loading.remove();

    // عرض رد Python
    addMessage(
      data.reply || "لم يصل رد من NORYN AI.",
      "ai"
    );

  } catch (error) {

    console.error("NORYN AI Error:", error);

    loading.textContent =
      "❌ حدث خطأ في الاتصال بـ NORYN AI.\n\n" +
      "تأكد من أن Node.js وPython يعملان على Render.";

  } finally {

    sendBtn.disabled = false;
    input.focus();

  }
}

// =========================
// زر الإرسال
// =========================

sendBtn.addEventListener("click", () => {
  sendMessage();
});

// =========================
// Enter للإرسال
// Shift + Enter لسطر جديد
// =========================

input.addEventListener("keydown", (event) => {

  if (event.key === "Enter" && !event.shiftKey) {

    event.preventDefault();

    sendMessage();

  }

});

// =========================
// الأزرار المقترحة
// =========================

document
  .querySelectorAll(".suggestion")
  .forEach((button) => {

    button.addEventListener("click", () => {

      const text = button.textContent.trim();

      sendMessage(text);

    });

  });

// =========================
// الوضع الليلي / النهاري
// =========================

const savedTheme =
  localStorage.getItem("noryn-theme");

if (savedTheme === "light") {

  document.body.classList.add("light");

  if (themeBtn) {
    themeBtn.textContent = "🌙";
  }

}

if (themeBtn) {

  themeBtn.addEventListener("click", () => {

    document.body.classList.toggle("light");

    const isLight =
      document.body.classList.contains("light");

    themeBtn.textContent =
      isLight ? "🌙" : "☀️";

    localStorage.setItem(
      "noryn-theme",
      isLight ? "light" : "dark"
    );

  });

}

// =========================
// تشغيل
// =========================

input.focus();
