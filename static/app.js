/* =========================================================
   NORYN AI v4.5
   Stable Chat + Memory + Markdown Renderer

   Features:
   - Conversation memory
   - Chat history
   - LocalStorage
   - General / Code / Learn / Write
   - Markdown rendering
   - Code blocks
   - Copy code button
   - New chat
   - Delete chat
   - Suggestions
   - Backend /api/chat
   ========================================================= */

(() => {
  "use strict";

  const STORAGE_KEY = "noryn_ai_chats_v45";

  const state = {
    mode: "general",
    busy: false,
    currentChatId: null,
    chats: []
  };

  /* =========================================================
     MODE PROMPTS
     ========================================================= */

  const MODE_PROMPTS = {
    general:
      "أنت NORYN AI، مساعد ذكي عام. أجب بوضوح وبالعربية عندما يكون السؤال بالعربية.",

    code:
      "أنت NORYN AI، مساعد متخصص في البرمجة. قدم كودًا صحيحًا وكاملًا وفسّر الحل باختصار.",

    learn:
      "أنت NORYN AI، مدرس ذكي. اشرح خطوة بخطوة وبطريقة بسيطة وتفاعل مع إجابات الطالب.",

    write:
      "أنت NORYN AI، مساعد للكتابة. ساعد في القصص والأفكار والتلخيص وإعادة الصياغة."
  };

  /* =========================================================
     HELPERS
     ========================================================= */

  function $(selector) {
    return document.querySelector(selector);
  }

  function createId() {
    return (
      "chat_" +
      Date.now() +
      "_" +
      Math.random().toString(36).slice(2, 9)
    );
  }

  function escapeText(text) {
    return String(text ?? "");
  }

  /* =========================================================
     MARKDOWN RENDERER
     ========================================================= */

  function renderMarkdown(container, text) {
    container.replaceChildren();

    const source = escapeText(text);
    const lines = source.split(/\r?\n/);

    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      /* -----------------------------------------------------
         Code block
         ----------------------------------------------------- */

      const fenceMatch = line.match(/^```([a-zA-Z0-9_+-]*)\s*$/);

      if (fenceMatch) {
        const language =
          fenceMatch[1] || "code";

        const codeLines = [];

        i++;

        while (
          i < lines.length &&
          !/^```\s*$/.test(lines[i])
        ) {
          codeLines.push(lines[i]);
          i++;
        }

        if (i < lines.length) {
          i++;
        }

        createCodeBlock(
          container,
          codeLines.join("\n"),
          language
        );

        continue;
      }

      /* -----------------------------------------------------
         Empty line
         ----------------------------------------------------- */

      if (!line.trim()) {
        const spacer = document.createElement("div");
        spacer.className = "md-spacer";
        container.appendChild(spacer);

        i++;
        continue;
      }

      /* -----------------------------------------------------
         Heading
         ----------------------------------------------------- */

      const headingMatch =
        line.match(/^(#{1,6})\s+(.+)$/);

      if (headingMatch) {
        const level = Math.min(
          headingMatch[1].length,
          6
        );

        const heading =
          document.createElement("h" + level);

        appendInlineContent(
          heading,
          headingMatch[2]
        );

        container.appendChild(heading);

        i++;
        continue;
      }

      /* -----------------------------------------------------
         Bullet list
         ----------------------------------------------------- */

      if (/^\s*[-*+]\s+/.test(line)) {
        const list =
          document.createElement("ul");

        while (
          i < lines.length &&
          /^\s*[-*+]\s+/.test(lines[i])
        ) {
          const item =
            document.createElement("li");

          const content =
            lines[i].replace(
              /^\s*[-*+]\s+/,
              ""
            );

          appendInlineContent(
            item,
            content
          );

          list.appendChild(item);
          i++;
        }

        container.appendChild(list);
        continue;
      }

      /* -----------------------------------------------------
         Numbered list
         ----------------------------------------------------- */

      if (/^\s*\d+\.\s+/.test(line)) {
        const list =
          document.createElement("ol");

        while (
          i < lines.length &&
          /^\s*\d+\.\s+/.test(lines[i])
        ) {
          const item =
            document.createElement("li");

          const content =
            lines[i].replace(
              /^\s*\d+\.\s+/,
              ""
            );

          appendInlineContent(
            item,
            content
          );

          list.appendChild(item);
          i++;
        }

        container.appendChild(list);
        continue;
      }

      /* -----------------------------------------------------
         Blockquote
         ----------------------------------------------------- */

      if (/^\s*>\s?/.test(line)) {
        const quote =
          document.createElement("blockquote");

        while (
          i < lines.length &&
          /^\s*>\s?/.test(lines[i])
        ) {
          const content =
            lines[i].replace(
              /^\s*>\s?/,
              ""
            );

          const paragraph =
            document.createElement("div");

          appendInlineContent(
            paragraph,
            content
          );

          quote.appendChild(paragraph);
          i++;
        }

        container.appendChild(quote);
        continue;
      }

      /* -----------------------------------------------------
         Normal paragraph
         ----------------------------------------------------- */

      const paragraph =
        document.createElement("p");

      appendInlineContent(
        paragraph,
        line
      );

      container.appendChild(paragraph);

      i++;
    }
  }

  /* =========================================================
     INLINE MARKDOWN
     ========================================================= */

  function appendInlineContent(parent, text) {
    const value = String(text ?? "");

    const tokenRegex =
      /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\))/g;

    let lastIndex = 0;
    let match;

    while (
      (match = tokenRegex.exec(value)) !== null
    ) {
      if (match.index > lastIndex) {
        parent.appendChild(
          document.createTextNode(
            value.slice(
              lastIndex,
              match.index
            )
          )
        );
      }

      const token = match[0];

      /* Bold */

      if (
        token.startsWith("**") ||
        token.startsWith("__")
      ) {
        const strong =
          document.createElement("strong");

        strong.textContent =
          token.slice(2, -2);

        parent.appendChild(strong);
      }

      /* Inline code */

      else if (
        token.startsWith("`")
      ) {
        const code =
          document.createElement("code");

        code.textContent =
          token.slice(1, -1);

        parent.appendChild(code);
      }

      /* Link */

      else if (
        token.startsWith("[")
      ) {
        const label =
          match[2];

        const url =
          match[3];

        const link =
          document.createElement("a");

        link.textContent = label;
        link.href = url;
        link.target = "_blank";
        link.rel =
          "noopener noreferrer";

        parent.appendChild(link);
      }

      lastIndex =
        tokenRegex.lastIndex;
    }

    if (lastIndex < value.length) {
      parent.appendChild(
        document.createTextNode(
          value.slice(lastIndex)
        )
      );
    }
  }

  /* =========================================================
     CODE BLOCK
     ========================================================= */

  function createCodeBlock(
    container,
    code,
    language
  ) {
    const wrapper =
      document.createElement("div");

    wrapper.className =
      "code-block";

    const header =
      document.createElement("div");

    header.className =
      "code-header";

    const lang =
      document.createElement("span");

    lang.className =
      "code-language";

    lang.textContent =
      language.toUpperCase();

    const copy =
      document.createElement("button");

    copy.type = "button";
    copy.className =
      "copy-code";

    copy.textContent =
      "📋 نسخ";

    copy.addEventListener(
      "click",
      async () => {
        try {
          await navigator.clipboard.writeText(
            code
          );

          copy.textContent =
            "✓ تم النسخ";

          setTimeout(() => {
            copy.textContent =
              "📋 نسخ";
          }, 1600);

        } catch (error) {
          console.error(
            "Copy error:",
            error
          );

          copy.textContent =
            "تعذر النسخ";
        }
      }
    );

    header.appendChild(lang);
    header.appendChild(copy);

    const pre =
      document.createElement("pre");

    const codeElement =
      document.createElement("code");

    codeElement.className =
      "language-" +
      language.toLowerCase();

    codeElement.textContent =
      code;

    pre.appendChild(
      codeElement
    );

    wrapper.appendChild(header);
    wrapper.appendChild(pre);

    container.appendChild(wrapper);
  }

  /* =========================================================
     LOAD / SAVE
     ========================================================= */

  function loadChats() {
    try {
      const raw =
        localStorage.getItem(
          STORAGE_KEY
        );

      const parsed =
        raw ? JSON.parse(raw) : [];

      state.chats =
        Array.isArray(parsed)
          ? parsed
          : [];

    } catch (error) {
      console.error(
        "NORYN load error:",
        error
      );

      state.chats = [];
    }
  }

  function saveChats() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(state.chats)
      );

    } catch (error) {
      console.error(
        "NORYN save error:",
        error
      );
    }
  }

  /* =========================================================
     CURRENT CHAT
     ========================================================= */

  function getCurrentChat() {
    return (
      state.chats.find(
        chat =>
          chat.id ===
          state.currentChatId
      ) || null
    );
  }

  /* =========================================================
     CLEAR
     ========================================================= */

  function clearMessages() {
    const messages =
      $("#messages");

    if (!messages) return;

    messages.replaceChildren();

    const welcome =
      document.createElement("div");

    welcome.className =
      "message ai";

    const welcomeText =
      document.createElement("div");

    welcomeText.textContent =
      "مرحبًا! أنا NORYN AI 🤖";

    const welcomeSub =
      document.createElement("div");

    welcomeSub.textContent =
      "كيف يمكنني مساعدتك؟";

    welcome.appendChild(
      welcomeText
    );

    welcome.appendChild(
      welcomeSub
    );

    messages.appendChild(
      welcome
    );
  }

  /* =========================================================
     ADD MESSAGE
     ========================================================= */

  function addMessage(
    text,
    type,
    save = true
  ) {
    const messages =
      $("#messages");

    if (!messages) return null;

    const item =
      document.createElement("div");

    item.className =
      "message " + type;

    /*
      إجابات AI تمر عبر Markdown renderer.
      رسائل المستخدم تبقى نصًا عاديًا.
    */

    if (type === "ai") {
      renderMarkdown(
        item,
        String(text)
      );
    } else {
      item.textContent =
        String(text);
    }

    messages.appendChild(item);

    messages.scrollTop =
      messages.scrollHeight;

    if (
      save &&
      (
        type === "user" ||
        type === "ai"
      )
    ) {
      const chat =
        getCurrentChat();

      if (chat) {
        if (
          !Array.isArray(
            chat.messages
          )
        ) {
          chat.messages = [];
        }

        chat.messages.push({
          type: type,
          text: String(text),
          time: Date.now()
        });

        chat.updatedAt =
          Date.now();

        if (
          type === "user" &&
          (
            !chat.title ||
            chat.title ===
              "محادثة جديدة"
          )
        ) {
          chat.title =
            String(text)
              .replace(/\s+/g, " ")
              .slice(0, 45);
        }

        saveChats();
        renderHistory();
      }
    }

    return item;
  }

  /* =========================================================
     RENDER CHAT
     ========================================================= */

  function renderChat(chat) {
    const messages =
      $("#messages");

    if (!messages) return;

    messages.replaceChildren();

    if (
      !chat ||
      !Array.isArray(
        chat.messages
      ) ||
      chat.messages.length === 0
    ) {
      clearMessages();
      return;
    }

    chat.messages.forEach(
      message => {
        addMessage(
          message.text,
          message.type,
          false
        );
      }
    );

    messages.scrollTop =
      messages.scrollHeight;
  }

  /* =========================================================
     MODE
     ========================================================= */

  function setMode(mode) {
    state.mode =
      mode || "general";

    document
      .querySelectorAll(
        "[data-mode]"
      )
      .forEach(button => {
        button.classList.toggle(
          "active",
          button.dataset.mode ===
            state.mode
        );
      });

    const input =
      $("#message");

    if (input) {
      const placeholders = {
        general:
          "اسأل NORYN عن أي شيء...",

        code:
          "اكتب مشكلة أو طلبًا برمجيًا...",

        learn:
          "ما الذي تريد أن تتعلمه؟",

        write:
          "ماذا تريد أن تكتب؟"
      };

      input.placeholder =
        placeholders[
          state.mode
        ] ||
        "اكتب رسالتك...";
    }

    const chat =
      getCurrentChat();

    if (chat) {
      chat.mode =
        state.mode;

      chat.updatedAt =
        Date.now();

      saveChats();
    }
  }

  /* =========================================================
     NEW CHAT
     ========================================================= */

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

    state.chats.unshift(
      chat
    );

    state.currentChatId =
      chat.id;

    setMode("general");

    clearMessages();

    saveChats();

    renderHistory();

    closeHistory();

    const input =
      $("#message");

    if (input) {
      input.value = "";
      input.focus();
    }
  }

  /* =========================================================
     OPEN CHAT
     ========================================================= */

  function openChat(id) {
    const chat =
      state.chats.find(
        item =>
          item.id === id
      );

    if (!chat) return;

    state.currentChatId =
      id;

    setMode(
      chat.mode ||
      "general"
    );

    renderChat(chat);

    closeHistory();

    const input =
      $("#message");

    if (input) {
      input.focus();
    }
  }

  /* =========================================================
     DELETE CHAT
     ========================================================= */

  function deleteChat(id) {
    const chat =
      state.chats.find(
        item =>
          item.id === id
      );

    if (!chat) return;

    const title =
      chat.title ||
      "هذه المحادثة";

    if (
      !window.confirm(
        "حذف " +
        title +
        "؟"
      )
    ) {
      return;
    }

    state.chats =
      state.chats.filter(
        item =>
          item.id !== id
      );

    if (
      state.currentChatId ===
      id
    ) {
      state.currentChatId =
        null;

      if (
        state.chats.length > 0
      ) {
        const next =
          state.chats
            .slice()
            .sort(
              (a, b) =>
                b.updatedAt -
                a.updatedAt
            )[0];

        state.currentChatId =
          next.id;

        setMode(
          next.mode ||
          "general"
        );

        renderChat(next);

      } else {
        createNewChat();
      }
    }

    saveChats();
    renderHistory();
  }

  /* =========================================================
     HISTORY UI
     ========================================================= */

  function renderHistory() {
    const list =
      $("#historyList");

    if (!list) return;

    list.replaceChildren();

    if (!state.chats.length) {
      const empty =
        document.createElement(
          "div"
        );

      empty.className =
        "empty-history";

      empty.textContent =
        "لا توجد محادثات محفوظة بعد.";

      list.appendChild(empty);

      return;
    }

    const sorted =
      state.chats
        .slice()
        .sort(
          (a, b) =>
            b.updatedAt -
            a.updatedAt
        );

    sorted.forEach(
      chat => {
        const row =
          document.createElement(
            "div"
          );

        row.className =
          "history-item";

        const open =
          document.createElement(
            "button"
          );

        open.type = "button";

        open.className =
          "history-open";

        const title =
          document.createElement(
            "div"
          );

        title.className =
          "history-title";

        title.textContent =
          chat.title ||
          "محادثة بدون عنوان";

        open.appendChild(title);

        open.addEventListener(
          "click",
          () => {
            openChat(chat.id);
          }
        );

        const remove =
          document.createElement(
            "button"
          );

        remove.type = "button";

        remove.className =
          "history-delete";

        remove.textContent =
          "🗑️";

        remove.setAttribute(
          "aria-label",
          "حذف المحادثة"
        );

        remove.addEventListener(
          "click",
          event => {
            event.stopPropagation();

            deleteChat(
              chat.id
            );
          }
        );

        row.appendChild(open);
        row.appendChild(remove);

        list.appendChild(row);
      }
    );
  }

  function openHistory() {
    const panel =
      $("#chatPanel");

    if (!panel) return;

    renderHistory();

    panel.classList.add(
      "open"
    );

    panel.setAttribute(
      "aria-hidden",
      "false"
    );
  }

  function closeHistory() {
    const panel =
      $("#chatPanel");

    if (!panel) return;

    panel.classList.remove(
      "open"
    );

    panel.setAttribute(
      "aria-hidden",
      "true"
    );
  }

  /* =========================================================
     BUSY
     ========================================================= */

  function setBusy(value) {
    state.busy =
      value;

    const send =
      $("#send");

    const input =
      $("#message");

    if (send) {
      send.disabled =
        value;

      send.textContent =
        value
          ? "..."
          : "إرسال";
    }

    if (input) {
      input.disabled =
        value;
    }
  }

  /* =========================================================
     CONVERSATION HISTORY
     ========================================================= */

  function getConversationHistory() {
    const chat =
      getCurrentChat();

    if (
      !chat ||
      !Array.isArray(
        chat.messages
      )
    ) {
      return [];
    }

    return chat.messages
      .filter(
        message => {
          return (
            (
              message.type ===
                "user" ||
              message.type ===
                "ai"
            ) &&
            String(
              message.text || ""
            ).trim()
          );
        }
      )
      .map(
        message => ({
          type:
            message.type,

          text:
            String(
              message.text
            )
        })
      );
  }

  /* =========================================================
     SEND MESSAGE
     ========================================================= */

  async function sendMessage() {
    if (state.busy)
      return;

    const input =
      $("#message");

    if (!input)
      return;

    const text =
      input.value.trim();

    if (!text)
      return;

    if (
      !state.currentChatId
    ) {
      createNewChat();
    }

    /*
      نأخذ الذاكرة قبل إضافة
      الرسالة الحالية حتى لا
      نرسلها مرتين.
    */

    const history =
      getConversationHistory();

    addMessage(
      text,
      "user",
      true
    );

    input.value = "";

    setBusy(true);

    const loading =
      addMessage(
        "⏳ NORYN يفكر...",
        "ai",
        false
      );

    try {
      const response =
        await fetch(
          "/api/chat",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              "Accept":
                "application/json"
            },

            body:
              JSON.stringify({
                message:
                  text,

                mode:
                  state.mode,

                system:
                  MODE_PROMPTS[
                    state.mode
                  ],

                history:
                  history
              })
          }
        );

      const raw =
        await response.text();

      const contentType =
        response.headers.get(
          "content-type"
        ) || "";

      if (!response.ok) {
        let serverMessage =
          "HTTP " +
          response.status;

        try {
          const errorData =
            JSON.parse(raw);

          serverMessage =
            errorData.error ||
            errorData.detail ||
            serverMessage;

        } catch (_) {}

        throw new Error(
          serverMessage
        );
      }

      if (
        !contentType.includes(
          "application/json"
        )
      ) {
        throw new Error(
          "الخادم أعاد HTML بدل JSON."
        );
      }

      let data;

      try {
        data =
          JSON.parse(raw);

      } catch (_) {
        throw new Error(
          "الخادم أعاد JSON غير صالح."
        );
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

      if (loading) {
        loading.remove();
      }

      addMessage(
        String(reply),
        "ai",
        true
      );

    } catch (error) {
      if (loading) {
        loading.remove();
      }

      console.error(
        "NORYN error:",
        error
      );

      addMessage(
        "❌ حدث خطأ في الاتصال بـ NORYN AI.\n\n" +
        (
          error.message ||
          "خطأ غير معروف"
        ),
        "ai",
        true
      );

    } finally {
      setBusy(false);

      if (input) {
        input.focus();
      }
    }
  }

  /* =========================================================
     SETUP
     ========================================================= */

  function setup() {
    if (
      window.__NORYN_V45_INITIALIZED__
    ) {
      return;
    }

    window.__NORYN_V45_INITIALIZED__ =
      true;

    loadChats();

    /* Modes */

    document
      .querySelectorAll(
        "[data-mode]"
      )
      .forEach(
        button => {
          button.addEventListener(
            "click",
            () => {
              setMode(
                button.dataset.mode ||
                "general"
              );
            }
          );
        }
      );

    /* Send */

    const send =
      $("#send");

    if (send) {
      send.addEventListener(
        "click",
        sendMessage
      );
    }

    /* Textarea */

    const input =
      $("#message");

    if (input) {
      input.addEventListener(
        "keydown",
        event => {
          if (
            event.key ===
              "Enter" &&
            !event.shiftKey
          ) {
            event.preventDefault();

            sendMessage();
          }
        }
      );
    }

    /* New Chat */

    const newChat =
      $("#newChat");

    if (newChat) {
      newChat.addEventListener(
        "click",
        event => {
          event.preventDefault();
          event.stopPropagation();

          createNewChat();
        }
      );
    }

    /* History */

    const historyButton =
      $("#historyButton");

    if (historyButton) {
      historyButton.addEventListener(
        "click",
        event => {
          event.preventDefault();
          event.stopPropagation();

          openHistory();
        }
      );
    }

    /* Close History */

    const closeButton =
      $("#closeHistory");

    if (closeButton) {
      closeButton.addEventListener(
        "click",
        event => {
          event.preventDefault();

          closeHistory();
        }
      );
    }

    /* New Chat inside panel */

    const panelNewChat =
      $("#panelNewChat");

    if (panelNewChat) {
      panelNewChat.addEventListener(
        "click",
        event => {
          event.preventDefault();

          createNewChat();
        }
      );
    }

    /* Click outside */

    const panel =
      $("#chatPanel");

    if (panel) {
      panel.addEventListener(
        "click",
        event => {
          if (
            event.target ===
            panel
          ) {
            closeHistory();
          }
        }
      );
    }

    /* Suggestions */

    document
      .querySelectorAll(
        ".suggestion"
      )
      .forEach(
        button => {
          button.addEventListener(
            "click",
            () => {
              const inputBox =
                $("#message");

              if (!inputBox)
                return;

              inputBox.value =
                button.dataset.prompt ||
                button.textContent.trim();

              inputBox.focus();
            }
          );
        }
      );

    /* Restore latest */

    if (
      state.chats.length > 0
    ) {
      const latest =
        state.chats
          .slice()
          .sort(
            (a, b) =>
              b.updatedAt -
              a.updatedAt
          )[0];

      state.currentChatId =
        latest.id;

      setMode(
        latest.mode ||
        "general"
      );

      renderChat(
        latest
      );

    } else {
      createNewChat();
    }

    renderHistory();
  }

  /* =========================================================
     INITIALIZATION
     ========================================================= */

  if (
    document.readyState ===
    "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      setup,
      {
        once: true
      }
    );
  } else {
    setup();
  }

})();
