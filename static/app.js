/* NORYN AI v4.1 - stable chat history
   Fixes:
   - Reliable initialization with readyState
   - New Chat button
   - Chat History button
   - LocalStorage history
   - Existing /api/chat connection
   - Reads backend "reply"
*/

(() => {
  "use strict";

  const STORAGE_KEY = "noryn_ai_chats_v41";

  const state = {
    mode: "general",
    busy: false,
    currentChatId: null,
    chats: []
  };

  const MODE_PROMPTS = {
    general: "أنت NORYN AI، مساعد ذكي عام. أجب بوضوح وبالعربية عندما يكون السؤال بالعربية.",
    code: "أنت NORYN AI، مساعد متخصص في البرمجة. قدم كودًا صحيحًا وفسّر الحل باختصار.",
    learn: "أنت NORYN AI، مساعد تعليمي. اشرح خطوة بخطوة وبطريقة بسيطة.",
    write: "أنت NORYN AI، مساعد للكتابة. ساعد في القصص والأفكار والتلخيص وإعادة الصياغة."
  };

  function $(selector) {
    return document.querySelector(selector);
  }

  function createId() {
    return "chat_" + Date.now() + "_" +
      Math.random().toString(36).slice(2, 9);
  }

  function loadChats() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      state.chats = Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error("NORYN load error:", error);
      state.chats = [];
    }
  }

  function saveChats() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.chats));
    } catch (error) {
      console.error("NORYN save error:", error);
    }
  }

  function getCurrentChat() {
    return state.chats.find(
      chat => chat.id === state.currentChatId
    ) || null;
  }

  function clearMessages() {
    const messages = $("#messages");
    if (!messages) return;

    messages.innerHTML = "";

    const welcome = document.createElement("div");
    welcome.className = "message ai";
    welcome.innerHTML =
      "مرحبًا! أنا NORYN AI 🤖<br>كيف يمكنني مساعدتك؟";

    messages.appendChild(welcome);
  }

  function addMessage(text, type, save = true) {
    const messages = $("#messages");
    if (!messages) return null;

    const item = document.createElement("div");
    item.className = "message " + type;
    item.textContent = String(text);

    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;

    if (save && (type === "user" || type === "ai")) {
      const chat = getCurrentChat();

      if (chat) {
        chat.messages.push({
          type: type,
          text: String(text),
          time: Date.now()
        });

        chat.updatedAt = Date.now();

        if (
          type === "user" &&
          (!chat.title || chat.title === "محادثة جديدة")
        ) {
          chat.title = String(text).slice(0, 45);
        }

        saveChats();
        renderHistory();
      }
    }

    return item;
  }

  function renderChat(chat) {
    const messages = $("#messages");
    if (!messages) return;

    messages.innerHTML = "";

    if (!chat || !Array.isArray(chat.messages) ||
        chat.messages.length === 0) {
      clearMessages();
      return;
    }

    chat.messages.forEach(message => {
      addMessage(message.text, message.type, false);
    });

    messages.scrollTop = messages.scrollHeight;
  }

  function setMode(mode) {
    state.mode = mode || "general";

    document.querySelectorAll("[data-mode]").forEach(button => {
      button.classList.toggle(
        "active",
        button.dataset.mode === state.mode
      );
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

    const chat = getCurrentChat();

    if (chat) {
      chat.mode = state.mode;
      chat.updatedAt = Date.now();
      saveChats();
    }
  }

  function createNewChat() {
    if (state.busy) return;

    const chat = {
      id: createId(),
      title: "محادثة جديدة",
      mode: "general",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: []
    };

    state.chats.unshift(chat);
    state.currentChatId = chat.id;

    setMode("general");
    clearMessages();
    saveChats();
    renderHistory();
    closeHistory();

    const input = $("#message");
    if (input) {
      input.value = "";
      input.focus();
    }
  }

  function openChat(id) {
    const chat = state.chats.find(item => item.id === id);
    if (!chat) return;

    state.currentChatId = id;
    setMode(chat.mode || "general");
    renderChat(chat);
    closeHistory();

    const input = $("#message");
    if (input) input.focus();
  }

  function deleteChat(id) {
    const chat = state.chats.find(item => item.id === id);
    if (!chat) return;

    const title = chat.title || "هذه المحادثة";

    if (!window.confirm("حذف " + title + "؟")) {
      return;
    }

    state.chats = state.chats.filter(item => item.id !== id);

    if (state.currentChatId === id) {
      state.currentChatId = null;

      if (state.chats.length > 0) {
        const next = state.chats
          .slice()
          .sort((a, b) => b.updatedAt - a.updatedAt)[0];

        state.currentChatId = next.id;
        setMode(next.mode || "general");
        renderChat(next);
      } else {
        createNewChat();
      }
    }

    saveChats();
    renderHistory();
  }

  function renderHistory() {
    const list = $("#historyList");
    if (!list) return;

    list.innerHTML = "";

    if (!state.chats.length) {
      const empty = document.createElement("div");
      empty.className = "empty-history";
      empty.textContent = "لا توجد محادثات محفوظة بعد.";
      list.appendChild(empty);
      return;
    }

    const sorted = state.chats
      .slice()
      .sort((a, b) => b.updatedAt - a.updatedAt);

    sorted.forEach(chat => {
      const row = document.createElement("div");
      row.className = "history-item";

      const open = document.createElement("button");
      open.type = "button";
      open.className = "history-open";

      const title = document.createElement("div");
      title.className = "history-title";
      title.textContent = chat.title || "محادثة بدون عنوان";

      open.appendChild(title);

      open.addEventListener("click", () => {
        openChat(chat.id);
      });

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "history-delete";
      remove.textContent = "🗑️";
      remove.setAttribute("aria-label", "حذف المحادثة");

      remove.addEventListener("click", event => {
        event.stopPropagation();
        deleteChat(chat.id);
      });

      row.appendChild(open);
      row.appendChild(remove);
      list.appendChild(row);
    });
  }

  function openHistory() {
    const panel = $("#chatPanel");
    if (!panel) return;

    renderHistory();
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
  }

  function closeHistory() {
    const panel = $("#chatPanel");
    if (!panel) return;

    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
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

    const text = input.value.trim();
    if (!text) return;

    if (!state.currentChatId) {
      createNewChat();
    }

    addMessage(text, "user", true);
    input.value = "";
    setBusy(true);

    const loading = addMessage("⏳ NORYN يفكر...", "ai", false);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({
          message: text,
          mode: state.mode,
          system: MODE_PROMPTS[state.mode]
        })
      });

      const raw = await response.text();
      const contentType =
        response.headers.get("content-type") || "";

      if (!response.ok) {
        throw new Error("HTTP " + response.status);
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

      const reply =
        data.reply ??
        data.answer ??
        data.response ??
        data.message ??
        data.text ??
        data.result ??
        data.output ??
        data.content;

      if (!reply) {
        throw new Error(
          data.error ||
          data.detail ||
          "لم نجد نص الإجابة."
        );
      }

      if (loading) loading.remove();

      addMessage(String(reply), "ai", true);

    } catch (error) {
      if (loading) loading.remove();

      console.error("NORYN error:", error);

      addMessage(
        "❌ حدث خطأ في الاتصال بـ NORYN AI.\n\n" +
        (error.message || "خطأ غير معروف"),
        "ai",
        true
      );
    } finally {
      setBusy(false);
      if (input) input.focus();
    }
  }

  function setup() {
    // Prevent duplicate initialization.
    if (window.__NORYN_V41_INITIALIZED__) return;
    window.__NORYN_V41_INITIALIZED__ = true;

    loadChats();

    document.querySelectorAll("[data-mode]").forEach(button => {
      button.addEventListener("click", () => {
        setMode(button.dataset.mode || "general");
      });
    });

    const send = $("#send");
    if (send) {
      send.addEventListener("click", sendMessage);
    }

    const input = $("#message");
    if (input) {
      input.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          sendMessage();
        }
      });
    }

    // New Chat
    const newChat = $("#newChat");
    if (newChat) {
      newChat.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        createNewChat();
      });
    }

    // History
    const historyButton = $("#historyButton");
    if (historyButton) {
      historyButton.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        openHistory();
      });
    }

    const closeButton = $("#closeHistory");
    if (closeButton) {
      closeButton.addEventListener("click", event => {
        event.preventDefault();
        closeHistory();
      });
    }

    const panelNewChat = $("#panelNewChat");
    if (panelNewChat) {
      panelNewChat.addEventListener("click", event => {
        event.preventDefault();
        createNewChat();
      });
    }

    const panel = $("#chatPanel");
    if (panel) {
      panel.addEventListener("click", event => {
        if (event.target === panel) {
          closeHistory();
        }
      });
    }

    document.querySelectorAll(".suggestion").forEach(button => {
      button.addEventListener("click", () => {
        const inputBox = $("#message");
        if (!inputBox) return;

        inputBox.value =
          button.dataset.prompt ||
          button.textContent.trim();

        inputBox.focus();
      });
    });

    if (state.chats.length > 0) {
      const latest = state.chats
        .slice()
        .sort((a, b) => b.updatedAt - a.updatedAt)[0];

      state.currentChatId = latest.id;
      setMode(latest.mode || "general");
      renderChat(latest);
    } else {
      createNewChat();
    }

    renderHistory();
  }

  // This works whether app.js loads before or after DOMContentLoaded.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup, {
      once: true
    });
  } else {
    setup();
  }

})();
