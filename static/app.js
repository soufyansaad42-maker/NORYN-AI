/* NORYN AI v4.1 - fixed response handling */
(() => {
  "use strict";

  const state = {
    mode: "general",
    busy: false
  };

  const MODE_PROMPTS = {
    general: "أنت NORYN AI، مساعد ذكي عام. أجب بوضوح وبالعربية عندما يكون السؤال بالعربية.",
    code: "أنت NORYN AI، مساعد متخصص في البرمجة. قدم كودًا صحيحًا وفسّر الحل باختصار.",
    learn: "أنت NORYN AI، مساعد تعليمي. اشرح خطوة بخطوة وبطريقة بسيطة.",
    write: "أنت NORYN AI، مساعد للكتابة. ساعد في القصص والأفكار والتلخيص وإعادة الصياغة."
  };

  const $ = (selector) => document.querySelector(selector);

  function addMessage(text, type) {
    const messages = $("#messages");
    if (!messages) return null;

    const item = document.createElement("div");
    item.className = `message ${type}`;
    item.textContent = text;

    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  function setBusy(value) {
    state.busy = value;

    const send = $("#send");
    const input = $("#message");

    if (send) {
      send.disabled = value;
      send.textContent = value ? "..." : "إرسال";
    }

    if (input) input.disabled = value;
  }

  async function sendMessage() {
    if (state.busy) return;

    const input = $("#message");
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";
    setBusy(true);

    const loading = addMessage("⏳ NORYN يفكر...", "ai");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({
          message: message,
          mode: state.mode,
          system: MODE_PROMPTS[state.mode]
        })
      });

      const contentType = response.headers.get("content-type") || "";
      const raw = await response.text();

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (!contentType.includes("application/json")) {
        throw new Error("الخادم أعاد HTML بدل JSON.");
      }

      let data;

      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error("الخادم أعاد JSON غير صالح.");
      }

      /*
       * مهم:
       * app.py يعيد الإجابة داخل المفتاح "reply".
       * كان app.js السابق لا يقرأ "reply"، ولذلك كان يظهر
       * "لم نجد نص الإجابة" رغم أن الخادم يرجع HTTP 200.
       */
      const answer =
        data.reply ??
        data.answer ??
        data.response ??
        data.message ??
        data.text ??
        data.result ??
        data.output ??
        data.content;

      if (!answer) {
        throw new Error(
          data.error ||
          data.detail ||
          "لم نجد نص الإجابة في رد الخادم."
        );
      }

      if (loading) loading.remove();

      addMessage(String(answer), "ai");

    } catch (error) {
      if (loading) loading.remove();

      console.error("NORYN AI error:", error);

      addMessage(
        "❌ حدث خطأ في الاتصال بـ NORYN AI.\n\n" +
        (error.message || "خطأ غير معروف"),
        "ai error"
      );
    } finally {
      setBusy(false);
      if (input) input.focus();
    }
  }

  function setupModes() {
    document.querySelectorAll("[data-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        state.mode = button.dataset.mode || "general";

        document.querySelectorAll("[data-mode]").forEach((item) => {
          item.classList.toggle("active", item === button);
        });

        const input = $("#message");

        if (input) {
          const placeholders = {
            general: "اسأل NORYN عن أي شيء...",
            code: "اكتب مشكلة أو طلبًا برمجيًا...",
            learn: "ما الذي تريد أن تتعلمه؟",
            write: "ماذا تريد أن تكتب؟"
          };

          input.placeholder =
            placeholders[state.mode] || "اكتب رسالتك...";
        }
      });
    });
  }

  function setupSend() {
    const send = $("#send");
    const input = $("#message");

    if (send) {
      send.addEventListener("click", sendMessage);
    }

    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          sendMessage();
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupModes();
    setupSend();
  });
})();
