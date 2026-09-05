const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send");
const messages = document.getElementById("messages");
const modeButtons = document.querySelectorAll("[data-mode]");

let currentMode = "general";

function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    messages.appendChild(message);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}

modeButtons.forEach(button => {
    button.addEventListener("click", () => {
        modeButtons.forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        currentMode = button.dataset.mode;
    });
});

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || sendButton.disabled) return;

    addMessage(message, "user");
    messageInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "⏳";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                message,
                mode: currentMode
            })
        });

        const contentType = response.headers.get("content-type") || "";
        let data;

        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error("Server returned non-JSON:", text);
            throw new Error("الخادم أعاد صفحة غير متوقعة بدل استجابة JSON.");
        }

        if (!response.ok || !data.ok) {
            throw new Error(data.error || `خطأ من الخادم (${response.status})`);
        }

        addMessage(data.reply, "ai");

    } catch (error) {
        console.error("NORYN AI:", error);
        addMessage("❌ " + error.message, "ai");
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "إرسال";
    }
}

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});
