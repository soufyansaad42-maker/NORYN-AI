/* NORYN AI v4.1
   Chat history + new chat + localStorage
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
        general:
            "أنت NORYN AI، مساعد ذكي عام. أجب بوضوح وبالعربية عندما يكون السؤال بالعربية.",

        code:
            "أنت NORYN AI، مساعد متخصص في البرمجة. قدم كودًا صحيحًا وفسّر الحل باختصار.",

        learn:
            "أنت NORYN AI، مساعد تعليمي. اشرح خطوة بخطوة وبطريقة بسيطة.",

        write:
            "أنت NORYN AI، مساعد للكتابة. ساعد في القصص والأفكار والتلخيص وإعادة الصياغة."
    };

    const $ = (selector) => document.querySelector(selector);

    function createId() {
        return "chat_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8);
    }

    function loadChats() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            state.chats = saved ? JSON.parse(saved) : [];
            if (!Array.isArray(state.chats)) state.chats = [];
        } catch (error) {
            console.error("NORYN storage error:", error);
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
        return state.chats.find(chat => chat.id === state.currentChatId) || null;
    }

    function createNewChat(silent = false) {
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
        state.mode = "general";

        saveChats();
        clearMessages();
        setModeButton("general");
        updateHistory();

        if (!silent) closeHistoryPanel();

        const input = $("#message");
        if (input) {
            input.value = "";
            input.placeholder = "اكتب رسالتك...";
            input.focus();
        }
    }

    function clearMessages() {
        const messages = $("#messages");
        if (!messages) return;

        messages.innerHTML = "";

        const welcome = document.createElement("div");
        welcome.className = "message ai";
        welcome.innerHTML = "مرحبًا! أنا NORYN AI 🤖<br>كيف يمكنني مساعدتك؟";

        messages.appendChild(welcome);
    }

    function renderMessages(chat) {
        const messages = $("#messages");
        if (!messages) return;

        messages.innerHTML = "";

        if (!chat || !chat.messages.length) {
            const welcome = document.createElement("div");
            welcome.className = "message ai";
            welcome.innerHTML = "مرحبًا! أنا NORYN AI 🤖<br>كيف يمكنني مساعدتك؟";
            messages.appendChild(welcome);
            return;
        }

        chat.messages.forEach(item => {
            addMessage(item.text, item.type, false);
        });

        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(text, type, save = true) {
        const messages = $("#messages");
        if (!messages) return null;

        const item = document.createElement("div");
        item.className = `message ${type}`;
        item.textContent = text;

        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;

        if (save && (type === "user" || type === "ai")) {
            const chat = getCurrentChat();

            if (chat) {
                chat.messages.push({
                    type,
                    text: String(text),
                    time: Date.now()
                });

                chat.updatedAt = Date.now();

                if (
                    type === "user" &&
                    chat.title === "محادثة جديدة"
                ) {
                    chat.title = String(text).slice(0, 45);
                }

                saveChats();
                updateHistory();
            }
        }

        return item;
    }

    function setModeButton(mode) {
        state.mode = mode;

        document.querySelectorAll("[data-mode]").forEach(button => {
            button.classList.toggle(
                "active",
                button.dataset.mode === mode
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
                placeholders[mode] || "اكتب رسالتك...";
        }
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

        if (!state.currentChatId) {
            createNewChat(true);
        }

        const chat = getCurrentChat();

        if (chat) {
            chat.mode = state.mode;
        }

        addMessage(message, "user");
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
                    message,
                    mode: state.mode,
                    system: MODE_PROMPTS[state.mode]
                })
            });

            const contentType =
                response.headers.get("content-type") || "";

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
                "ai"
            );
        } finally {
            setBusy(false);
            if (input) input.focus();
        }
    }

    function openHistoryPanel() {
        const panel = $("#chatPanel");
        if (!panel) return;

        updateHistory();
        panel.classList.add("open");
        panel.setAttribute("aria-hidden", "false");
    }

    function closeHistoryPanel() {
        const panel = $("#chatPanel");
        if (!panel) return;

        panel.classList.remove("open");
        panel.setAttribute("aria-hidden", "true");
    }

    function updateHistory() {
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

        state.chats
            .slice()
            .sort((a, b) => b.updatedAt - a.updatedAt)
            .forEach(chat => {
                const row = document.createElement("div");
                row.className = "history-item";

                const openButton = document.createElement("button");
                openButton.type = "button";
                openButton.className = "history-open";

                const title = document.createElement("div");
                title.className = "history-title";
                title.textContent = chat.title || "محادثة بدون عنوان";

                openButton.appendChild(title);

                openButton.addEventListener("click", () => {
                    openChat(chat.id);
                });

                const deleteButton = document.createElement("button");
                deleteButton.type = "button";
                deleteButton.className = "history-delete";
                deleteButton.textContent = "🗑️";
                deleteButton.setAttribute("aria-label", "حذف المحادثة");

                deleteButton.addEventListener("click", (event) => {
                    event.stopPropagation();
                    deleteChat(chat.id);
                });

                row.appendChild(openButton);
                row.appendChild(deleteButton);

                list.appendChild(row);
            });
    }

    function openChat(id) {
        const chat = state.chats.find(item => item.id === id);
        if (!chat) return;

        state.currentChatId = chat.id;

        setModeButton(chat.mode || "general");
        renderMessages(chat);
        closeHistoryPanel();

        const input = $("#message");
        if (input) input.focus();
    }

    function deleteChat(id) {
        const chat = state.chats.find(item => item.id === id);
        if (!chat) return;

        const confirmed = window.confirm(
            `هل تريد حذف "${chat.title || "هذه المحادثة"}"؟`
        );

        if (!confirmed) return;

        state.chats = state.chats.filter(item => item.id !== id);

        if (state.currentChatId === id) {
            state.currentChatId = null;
            clearMessages();
        }

        saveChats();
        updateHistory();
    }

    function setupModes() {
        document.querySelectorAll("[data-mode]").forEach(button => {
            button.addEventListener("click", () => {
                setModeButton(button.dataset.mode || "general");

                const chat = getCurrentChat();
                if (chat) {
                    chat.mode = state.mode;
                    chat.updatedAt = Date.now();
                    saveChats();
                }
            });
        });
    }

    function setupSuggestions() {
        const input = $("#message");
        if (!input) return;

        document.querySelectorAll(".suggestion").forEach(button => {
            button.addEventListener("click", () => {
                input.value =
                    button.dataset.prompt ||
                    button.textContent.trim();

                input.focus();
                input.setSelectionRange(
                    input.value.length,
                    input.value.length
                );
            });
        });
    }

    function setupButtons() {
        const send = $("#send");
        const input = $("#message");

        if (send) {
            send.addEventListener("click", sendMessage);
        }

        if (input) {
            input.addEventListener("keydown", event => {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            });
        }

        const historyButton = $("#historyButton");
        if (historyButton) {
            historyButton.addEventListener(
                "click",
                openHistoryPanel
            );
        }

        const closeHistory = $("#closeHistory");
        if (closeHistory) {
            closeHistory.addEventListener(
                "click",
                closeHistoryPanel
            );
        }

        const newChat = $("#newChat");
        if (newChat) {
            newChat.addEventListener(
                "click",
                () => createNewChat(false)
            );
        }

        const panelNewChat = $("#panelNewChat");
        if (panelNewChat) {
            panelNewChat.addEventListener(
                "click",
                () => createNewChat(false)
            );
        }

        const panel = $("#chatPanel");
        if (panel) {
            panel.addEventListener("click", event => {
                if (event.target === panel) {
                    closeHistoryPanel();
                }
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        loadChats();

        if (state.chats.length) {
            const newest = state.chats
                .slice()
                .sort((a, b) => b.updatedAt - a.updatedAt)[0];

            openChat(newest.id);
        } else {
            createNewChat(true);
        }

        setupModes();
        setupSuggestions();
        setupButtons();
        updateHistory();
    });
})();
