const chat = document.getElementById("chat");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const themeBtn = document.getElementById("themeBtn");

const API_URL = "http://localhost:3000/api/chat";

async function sendMessage(text = null) {
  const message = text || input.value.trim();
  if (!message) return;

  const welcome = document.getElementById("welcome");
  if (welcome) welcome.remove();

  addMessage(message, "user");
  input.value = "";
  resizeTextarea();

  const loading = addMessage("NORYN AI يفكر عبر Python... ⏳", "ai");

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    });

    const data = await response.json();
    loading.remove();

    if (!response.ok) {
      throw new Error(data.error || "حدث خطأ في الخادم");
    }

    addMessage(data.reply, "ai");
  } catch (error) {
    loading.remove();
    addMessage(
      "تعذر الاتصال بالسلسلة الكاملة. تأكد من تشغيل Node.js وPython.\n\n" +
      error.message,
      "ai"
    );
  }
}

function addMessage(text, type) {
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

sendBtn.addEventListener("click", () => sendMessage());

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

input.addEventListener("input", resizeTextarea);

function resizeTextarea() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 130) + "px";
}

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    const text = button.textContent.replace(/^[^\p{L}\p{N}]+/u, "").trim();
    sendMessage(text);
  });
});

const savedTheme = localStorage.getItem("noryn-theme");

if (savedTheme === "light") {
  document.body.classList.add("light");
  themeBtn.textContent = "🌙";
}

themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("light");

  const isLight = document.body.classList.contains("light");
  themeBtn.textContent = isLight ? "🌙" : "☀️";

  localStorage.setItem("noryn-theme", isLight ? "light" : "dark");
});
