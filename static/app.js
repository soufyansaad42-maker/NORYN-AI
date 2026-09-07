/* =========================================================
   NORYN AI v4.5
   Modern Chat UI
   - Conversation memory
   - Chat history
   - Markdown rendering
   - Copy response
   - Regenerate response
   - Like / Dislike
   - Mobile first
   - No AI response card
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


  /* =======================================================
     Helpers
  ======================================================= */

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


  /* =======================================================
     Escape HTML
  ======================================================= */

  function escapeHTML(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }


  /* =======================================================
     Unescape HTML
     يستخدم فقط لاستعادة الكود الأصلي (للنسخ)
     من نص تم تهريبه مسبقًا عبر escapeHTML
  ======================================================= */

  function unescapeHTML(value) {
    return String(value)
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, "\"")
      .replace(/&#039;/g, "'");
  }


  /* =======================================================
     Markdown Renderer
     بسيط وآمن بدون مكتبات خارجية
  ======================================================= */

  function renderMarkdown(text) {
    let html = escapeHTML(text || "");

    /* =====================================================
       Code blocks
       -----------------------------------------------------
       مهم جدًا: نستخرج كتل الكود ونستبدلها بعلامة مؤقتة
       (placeholder) قبل تطبيق أي تحويلات Markdown أخرى
       (bold, headings, lists, line breaks...).
       لو تركنا كتلة الكود الحقيقية داخل html، فإن التحويلات
       اللاحقة تشتغل عليها بالغلط وتكسرها، مثال:
         - سطر "* {" في CSS reset يتحول إلى <li>{</li>
         - "# " في تعليقات Python أو CSS ids تتحول إلى <h1>
         - "\n" يتحول إلى <br> فيكسر تنسيق الكود
         - backtick مفردة (template literals) تتحول inline code
       لذلك نخفي الكود مؤقتًا، ونطبق باقي التحويلات، ثم نعيده
       في النهاية كما هو دون أي مساس.
    ===================================================== */

    const codeBlocks = [];

    html = html.replace(
      /```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g,
      (_, language, code) => {
        const lang = language
          ? `<span class="code-language">${escapeHTML(language)}</span>`
          : "";

        /* code هنا مُهرّب أصلًا (لأنه جزء من html المُهرّب) */
        /* نعيده لأصله فقط لغرض النسخ، وليس للعرض */

        const rawCode = unescapeHTML(code);

        const blockHtml = `
          <div class="noryn-code">
            <div class="code-head">
              <span>${lang}</span>
              <button
                type="button"
                class="code-copy"
                data-code="${encodeURIComponent(rawCode)}"
              >
                نسخ
              </button>
            </div>
            <pre><code>${code}</code></pre>
          </div>
        `;

        const token = `@@NORYN_CODE_BLOCK_${codeBlocks.length}@@`;

        codeBlocks.push(blockHtml);

        return token;
      }
    );

    /* Inline code */

    html = html.replace(
      /`([^`\n]+)`/g,
      "<code class=\"inline-code\">$1</code>"
    );

    /* Bold */

    html = html.replace(
      /\*\*(.+?)\*\*/g,
      "<strong>$1</strong>"
    );

    /* Headings */

    html = html.replace(
      /^### (.+)$/gm,
      "<h3>$1</h3>"
    );

    html = html.replace(
      /^## (.+)$/gm,
      "<h2>$1</h2>"
    );

    html = html.replace(
      /^# (.+)$/gm,
      "<h1>$1</h1>"
    );

    /* Bullet lists */

    html = html.replace(
      /^(?:[-*]) (.+)$/gm,
      "<li>$1</li>"
    );

    html = html.replace(
      /(<li>.*<\/li>)/gs,
      "<ul>$1</ul>"
    );

    /* Numbered lists */

    html = html.replace(
      /^\d+\.\s(.+)$/gm,
      "<li>$1</li>"
    );

    /* Line breaks */

    html = html.replace(/\n/g, "<br>");

    /* استعادة كتل الكود الحقيقية بعد انتهاء كل التحويلات */

    codeBlocks.forEach((blockHtml, index) => {

      const token = `@@NORYN_CODE_BLOCK_${index}@@`;

      html = html.split(token).join(blockHtml);
    });

    return html;
  }


  /* =======================================================
     Load / Save
  ======================================================= */

  function loadChats() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];

      state.chats = Array.isArray(parsed)
        ? parsed
        : [];

    } catch (error) {
      console.error("NORYN load error:", error);
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
      console.error("NORYN save error:", error);
    }
  }


  /* =======================================================
     Current Chat
  ======================================================= */

  function getCurrentChat() {
    return (
      state.chats.find(
        chat => chat.id === state.currentChatId
      ) || null
    );
  }


  /* =======================================================
     Clear Messages
  ======================================================= */

  function clearMessages() {
    const messages = $("#messages");

    if (!messages) return;

    messages.innerHTML = "";

    const welcome = document.createElement("div");

    welcome.className = "message ai welcome-message";

    welcome.innerHTML = `
      <div class="message-content">
        مرحبًا! أنا NORYN AI 🤖<br>
        كيف يمكنني مساعدتك؟
      </div>
    `;

    messages.appendChild(welcome);
  }


  /* =======================================================
     Create AI Actions
  ======================================================= */

  function createActions(messageObject) {

    const actions = document.createElement("div");

    actions.className = "message-actions";

    /* Regenerate */

    const regenerate = document.createElement("button");

    regenerate.type = "button";
    regenerate.className = "message-action regenerate";
    regenerate.innerHTML = "↻ <span>إعادة الرد</span>";

    regenerate.addEventListener("click", () => {
      regenerateResponse(messageObject);
    });


    /* Copy */

    const copy = document.createElement("button");

    copy.type = "button";
    copy.className = "message-action copy-response";

    copy.innerHTML = "📋 <span>نسخ</span>";

    copy.addEventListener("click", async () => {

      const success = await copyText(
        messageObject.text
      );

      if (success) {
        copy.innerHTML = "✓ <span>تم النسخ</span>";

        setTimeout(() => {
          copy.innerHTML = "📋 <span>نسخ</span>";
        }, 1500);
      }
    });


    /* Like */

    const like = document.createElement("button");

    like.type = "button";
    like.className = "message-action feedback-like";
    like.innerHTML = "👍";

    like.addEventListener("click", () => {

      messageObject.feedback =
        messageObject.feedback === "like"
          ? null
          : "like";

      saveChats();

      updateFeedbackButtons(
        actions,
        messageObject
      );
    });


    /* Dislike */

    const dislike = document.createElement("button");

    dislike.type = "button";
    dislike.className =
      "message-action feedback-dislike";

    dislike.innerHTML = "👎";

    dislike.addEventListener("click", () => {

      messageObject.feedback =
        messageObject.feedback === "dislike"
          ? null
          : "dislike";

      saveChats();

      updateFeedbackButtons(
        actions,
        messageObject
      );
    });


    actions.appendChild(regenerate);
    actions.appendChild(copy);
    actions.appendChild(like);
    actions.appendChild(dislike);

    updateFeedbackButtons(
      actions,
      messageObject
    );

    return actions;
  }


  /* =======================================================
     Feedback State
  ======================================================= */

  function updateFeedbackButtons(
    actions,
    messageObject
  ) {

    const like =
      actions.querySelector(
        ".feedback-like"
      );

    const dislike =
      actions.querySelector(
        ".feedback-dislike"
      );

    if (like) {
      like.classList.toggle(
        "selected",
        messageObject.feedback === "like"
      );
    }

    if (dislike) {
      dislike.classList.toggle(
        "selected",
        messageObject.feedback === "dislike"
      );
    }
  }


  /* =======================================================
     Copy
  ======================================================= */

  async function copyText(text) {

    try {

      if (
        navigator.clipboard &&
        window.isSecureContext
      ) {

        await navigator.clipboard.writeText(
          String(text)
        );

        return true;
      }

      const textarea =
        document.createElement("textarea");

      textarea.value = String(text);

      textarea.style.position = "fixed";
      textarea.style.opacity = "0";

      document.body.appendChild(textarea);

      textarea.select();

      const success =
        document.execCommand("copy");

      textarea.remove();

      return success;

    } catch (error) {

      console.error(
        "Copy error:",
        error
      );

      return false;
    }
  }


  /* =======================================================
     Add Message
  ======================================================= */

  function addMessage(
    text,
    type,
    save = true,
    messageObject = null
  ) {

    const messages = $("#messages");

    if (!messages) return null;


    const row =
      document.createElement("div");

    row.className =
      "message-row " + type;


    const item =
      document.createElement("div");

    item.className =
      "message " + type;


    if (type === "ai") {

      const content =
        document.createElement("div");

      content.className =
        "message-content";

      content.innerHTML =
        renderMarkdown(text);

      item.appendChild(content);

      row.appendChild(item);


      if (messageObject) {

        const actions =
          createActions(messageObject);

        row.appendChild(actions);
      }

    } else {

      item.textContent =
        String(text);

      row.appendChild(item);
    }


    messages.appendChild(row);

    messages.scrollTop =
      messages.scrollHeight;


    /* Code copy buttons */

    row.querySelectorAll(
      ".code-copy"
    ).forEach(button => {

      button.addEventListener(
        "click",
        async () => {

          const code =
            decodeURIComponent(
              button.dataset.code || ""
            );

          const success =
            await copyText(code);

          if (success) {

            button.textContent =
              "تم النسخ";

            setTimeout(() => {
              button.textContent =
                "نسخ";
            }, 1500);
          }
        }
      );

    });


    /* Save */

    if (
      save &&
      (type === "user" ||
       type === "ai")
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


        const msg =
          messageObject || {
            type,
            text: String(text),
            time: Date.now()
          };


        chat.messages.push(msg);

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


    return row;
  }


  /* =======================================================
     Render Chat
  ======================================================= */

  function renderChat(chat) {

    const messages =
      $("#messages");

    if (!messages) return;

    messages.innerHTML = "";


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
          false,
          message.type === "ai"
            ? message
            : null
        );

      }
    );


    messages.scrollTop =
      messages.scrollHeight;
  }


  /* =======================================================
     Mode
  ======================================================= */

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
        placeholders[state.mode] ||
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


  /* =======================================================
     New Chat
  ======================================================= */

  function createNewChat() {

    if (state.busy)
      return;


    const chat = {

      id: createId(),

      title:
        "محادثة جديدة",

      mode:
        "general",

      createdAt:
        Date.now(),

      updatedAt:
        Date.now(),

      messages: []
    };


    state.chats.unshift(chat);

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


  /* =======================================================
     Open Chat
  ======================================================= */

  function openChat(id) {

    const chat =
      state.chats.find(
        item =>
          item.id === id
      );


    if (!chat)
      return;


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


    if (input)
      input.focus();
  }


  /* =======================================================
     Delete Chat
  ======================================================= */

  function deleteChat(id) {

    const chat =
      state.chats.find(
        item =>
          item.id === id
      );


    if (!chat)
      return;


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


  /* =======================================================
     History
  ======================================================= */

  function renderHistory() {

    const list =
      $("#historyList");


    if (!list)
      return;


    list.innerHTML = "";


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


    sorted.forEach(chat => {

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


      open.type =
        "button";

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


      remove.type =
        "button";

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

    });
  }


  function openHistory() {

    const panel =
      $("#chatPanel");


    if (!panel)
      return;


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


    if (!panel)
      return;


    panel.classList.remove(
      "open"
    );


    panel.setAttribute(
      "aria-hidden",
      "true"
    );
  }


  /* =======================================================
     Busy
  ======================================================= */

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


  /* =======================================================
     Conversation History
  ======================================================= */

  function getConversationHistory(
    chat = getCurrentChat()
  ) {

    if (
      !chat ||
      !Array.isArray(
        chat.messages
      )
    ) {
      return [];
    }


    return chat.messages
      .filter(message => {

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

      })
      .map(message => ({

        type:
          message.type,

        text:
          String(
            message.text
          )
      }));
  }


  /* =======================================================
     Request AI
  ======================================================= */

  async function requestAI(
    message,
    history
  ) {

    const response =
      await fetch(
        "/api/chat",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",

            "Accept":
              "application/json"
          },

          body:
            JSON.stringify({

              message:
                message,

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


    return String(reply);
  }


  /* =======================================================
     Send Message
  ======================================================= */

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

      const reply =
        await requestAI(
          text,
          history
        );


      if (loading) {

        loading.remove();
      }


      const messageObject = {

        type:
          "ai",

        text:
          reply,

        time:
          Date.now(),

        feedback:
          null
      };


      addMessage(
        reply,
        "ai",
        true,
        messageObject
      );


    } catch (error) {

      if (loading) {

        loading.remove();
      }


      console.error(
        "NORYN error:",
        error
      );


      const errorText =
        "❌ حدث خطأ في الاتصال بـ NORYN AI.\n\n" +
        (
          error.message ||
          "خطأ غير معروف"
        );


      const messageObject = {

        type:
          "ai",

        text:
          errorText,

        time:
          Date.now(),

        feedback:
          null
      };


      addMessage(
        errorText,
        "ai",
        true,
        messageObject
      );

    } finally {

      setBusy(false);


      if (input) {

        input.focus();
      }
    }
  }


  /* =======================================================
     Regenerate Response
  ======================================================= */

  async function regenerateResponse(
    targetMessage
  ) {

    if (state.busy)
      return;


    const chat =
      getCurrentChat();


    if (!chat ||
        !Array.isArray(
          chat.messages
        )
    ) {
      return;
    }


    const aiIndex =
      chat.messages.indexOf(
        targetMessage
      );


    if (aiIndex === -1)
      return;


    /* نبحث عن سؤال المستخدم السابق */

    let userIndex =
      aiIndex - 1;


    while (
      userIndex >= 0 &&
      chat.messages[userIndex].type !==
        "user"
    ) {

      userIndex--;
    }


    if (userIndex < 0)
      return;


    const userMessage =
      chat.messages[userIndex];


    /* التاريخ قبل السؤال */

    const history =
      chat.messages
        .slice(0, userIndex)
        .filter(message =>
          (
            message.type === "user" ||
            message.type === "ai"
          )
        )
        .map(message => ({
          type:
            message.type,

          text:
            String(
              message.text
            )
        }));


    setBusy(true);


    const row =
      findMessageRow(
        targetMessage
      );


    let oldContent = null;


    if (row) {

      oldContent =
        row.querySelector(
          ".message-content"
        );


      if (oldContent) {

        oldContent.innerHTML =
          "⏳ NORYN يعيد التفكير...";
      }


      const actions =
        row.querySelector(
          ".message-actions"
        );


      if (actions) {

        actions.remove();
      }
    }


    try {

      const reply =
        await requestAI(
          userMessage.text,
          history
        );


      targetMessage.text =
        reply;


      targetMessage.time =
        Date.now();


      targetMessage.feedback =
        null;


      chat.updatedAt =
        Date.now();


      saveChats();


      if (row) {

        const content =
          row.querySelector(
            ".message-content"
          );


        if (content) {

          content.innerHTML =
            renderMarkdown(
              reply
            );
        }


        const oldActions =
          row.querySelector(
            ".message-actions"
          );


        if (oldActions) {
          oldActions.remove();
        }


        row.appendChild(
          createActions(
            targetMessage
          )
        );


        setupCodeButtons(row);
      }


      renderHistory();


    } catch (error) {

      console.error(
        "Regenerate error:",
        error
      );


      if (row) {

        const content =
          row.querySelector(
            ".message-content"
          );


        if (content) {

          content.textContent =
            "❌ تعذر إعادة الرد.\n\n" +
            (
              error.message ||
              "خطأ غير معروف"
            );
        }


        row.appendChild(
          createActions(
            targetMessage
          )
        );
      }

    } finally {

      setBusy(false);
    }
  }


  /* =======================================================
     Find Message Row
  ======================================================= */

  function findMessageRow(
    messageObject
  ) {

    const rows =
      document.querySelectorAll(
        "#messages .message-row.ai"
      );


    const chat =
      getCurrentChat();


    if (!chat)
      return null;


    const aiMessages =
      chat.messages.filter(
        message =>
          message.type === "ai"
      );


    const index =
      aiMessages.indexOf(
        messageObject
      );


    if (
      index < 0 ||
      index >= rows.length
    ) {
      return null;
    }


    return rows[index];
  }


  /* =======================================================
     Code Buttons
  ======================================================= */

  function setupCodeButtons(
    root
  ) {

    root
      .querySelectorAll(
        ".code-copy"
      )
      .forEach(button => {

        if (
          button.dataset.ready ===
          "true"
        ) {
          return;
        }


        button.dataset.ready =
          "true";


        button.addEventListener(
          "click",
          async () => {

            const code =
              decodeURIComponent(
                button.dataset.code ||
                ""
              );


            const success =
              await copyText(
                code
              );


            if (success) {

              button.textContent =
                "تم النسخ";


              setTimeout(() => {

                button.textContent =
                  "نسخ";

              }, 1500);
            }
          }
        );
      });
  }


  /* =======================================================
     Setup
  ======================================================= */

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
      .forEach(button => {

        button.addEventListener(
          "click",
          () => {

            setMode(
              button.dataset.mode ||
              "general"
            );
          }
        );
      });


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


    /* Close */

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


    /* New Chat in panel */

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


    /* Click outside panel */

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
      .forEach(button => {

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
      });


    /* Restore latest chat */

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


  /* =======================================================
     Initialization
  ======================================================= */

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
