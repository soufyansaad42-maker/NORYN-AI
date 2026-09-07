/* =========================================================
   NORYN AI v7
   SEARCH + WRITE

   Features:
   - Search mode
   - Write mode
   - Chat history
   - LocalStorage
   - Conversation memory
   - New chat
   - Delete chat
   - Dark / Light theme
   - Temporary chat
   - Memory toggle
   - Suggestions
   - Settings panel
   - Voice input when supported
   - File selection
   - Backend /api/chat
========================================================= */

(() => {
    "use strict";

    const STORAGE_KEY = "noryn_ai_v7_chats";
    const SETTINGS_KEY = "noryn_ai_v7_settings";

    const state = {
        mode: "search",
        busy: false,
        currentChatId: null,
        chats: [],
        temporaryChat: false,
        memoryEnabled: true,
        darkMode: false
    };


    /* =========================================================
       Helpers
    ========================================================= */

    function $(selector) {
        return document.querySelector(selector);
    }

    function $all(selector) {
        return document.querySelectorAll(selector);
    }

    function createId() {
        return (
            "chat_" +
            Date.now() +
            "_" +
            Math.random().toString(36).slice(2, 9)
        );
    }

    function showToast(message) {
        const toast = $("#toast");

        if (!toast) return;

        toast.textContent = message;
        toast.classList.add("show");

        clearTimeout(showToast.timer);

        showToast.timer = setTimeout(() => {
            toast.classList.remove("show");
        }, 2500);
    }


    /* =========================================================
       Settings
    ========================================================= */

    function loadSettings() {
        try {
            const raw = localStorage.getItem(SETTINGS_KEY);

            if (!raw) return;

            const settings = JSON.parse(raw);

            state.temporaryChat =
                Boolean(settings.temporaryChat);

            state.memoryEnabled =
                settings.memoryEnabled !== false;

            state.darkMode =
                Boolean(settings.darkMode);

        } catch (error) {
            console.error(
                "NORYN settings load error:",
                error
            );
        }

        applyTheme();
        updateSettingsUI();
    }


    function saveSettings() {
        try {
            localStorage.setItem(
                SETTINGS_KEY,
                JSON.stringify({
                    temporaryChat:
                        state.temporaryChat,

                    memoryEnabled:
                        state.memoryEnabled,

                    darkMode:
                        state.darkMode
                })
            );
        } catch (error) {
            console.error(
                "NORYN settings save error:",
                error
            );
        }
    }


    function applyTheme() {
        document.body.classList.toggle(
            "dark",
            state.darkMode
        );
    }


    function updateSettingsUI() {
        const themeToggle = $("#themeToggle");
        const temporaryToggle =
            $("#temporaryChatToggle");
        const memoryToggle =
            $("#memoryToggle");

        if (themeToggle) {
            themeToggle.textContent =
                state.darkMode
                    ? "الوضع الفاتح"
                    : "الوضع الداكن";
        }

        if (temporaryToggle) {
            temporaryToggle.textContent =
                state.temporaryChat
                    ? "إيقاف"
                    : "تشغيل";
        }

        if (memoryToggle) {
            memoryToggle.textContent =
                state.memoryEnabled
                    ? "إيقاف"
                    : "تشغيل";
        }
    }


    /* =========================================================
       Chats
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
                "NORYN chats load error:",
                error
            );

            state.chats = [];
        }
    }


    function saveChats() {
        if (state.temporaryChat) {
            return;
        }

        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(state.chats)
            );
        } catch (error) {
            console.error(
                "NORYN chats save error:",
                error
            );
        }
    }


    function getCurrentChat() {
        return (
            state.chats.find(
                chat =>
                    chat.id ===
                    state.currentChatId
            ) || null
        );
    }


    function createNewChat() {
        if (state.busy) return;

        const chat = {
            id: createId(),

            title:
                state.mode === "write"
                    ? "كتابة جديدة"
                    : "بحث جديد",

            mode: state.mode,

            createdAt: Date.now(),

            updatedAt: Date.now(),

            messages: []
        };

        state.chats.unshift(chat);

        state.currentChatId =
            chat.id;

        clearMessages();

        renderHistory();

        if (!state.temporaryChat) {
            saveChats();
        }

        closeAllPanels();

        const input = $("#message");

        if (input) {
            input.value = "";
            input.focus();
        }
    }


    function deleteChat(id) {
        const chat =
            state.chats.find(
                item => item.id === id
            );

        if (!chat) return;

        const title =
            chat.title ||
            "هذه المحادثة";

        if (
            !window.confirm(
                "حذف " + title + "؟"
            )
        ) {
            return;
        }

        state.chats =
            state.chats.filter(
                item => item.id !== id
            );

        if (
            state.currentChatId === id
        ) {
            state.currentChatId = null;

            if (state.chats.length) {
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
                    "search"
                );

                renderChat(latest);

            } else {
                createNewChat();
            }
        }

        saveChats();
        renderHistory();

        showToast(
            "تم حذف المحادثة"
        );
    }


    /* =========================================================
       Messages
    ========================================================= */

    function clearMessages() {
        const messages =
            $("#messages");

        if (!messages) return;

        messages.innerHTML = "";

        const welcome =
            document.createElement(
                "div"
            );

        welcome.className =
            "message ai welcome-message";

        welcome.innerHTML = `
            <div class="message-content">
                <p>
                    مرحبًا! أنا
                    <strong>NORYN AI</strong> 🤖
                </p>

                <p>
                    هل تريد البحث عن معلومة
                    أم كتابة محتوى؟
                </p>
            </div>
        `;

        messages.appendChild(
            welcome
        );
    }


    function addMessage(
        text,
        type,
        save = true
    ) {
        const messages =
            $("#messages");

        if (!messages) return null;

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "message " + type;

        const content =
            document.createElement(
                "div"
            );

        content.className =
            "message-content";

        content.textContent =
            String(text);

        item.appendChild(content);

        messages.appendChild(item);

        messages.scrollTop =
            messages.scrollHeight;


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

                chat.messages.push({
                    type,
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
                            "بحث جديد" ||
                        chat.title ===
                            "كتابة جديدة"
                    )
                ) {
                    chat.title =
                        String(text)
                            .replace(
                                /\s+/g,
                                " "
                            )
                            .slice(0, 50);
                }

                saveChats();

                renderHistory();
            }
        }

        return item;
    }


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
            !chat.messages.length
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
       Mode
    ========================================================= */

    function setMode(mode) {
        state.mode =
            mode === "write"
                ? "write"
                : "search";

        $all("[data-mode]")
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

            input.placeholder =
                state.mode === "write"
                    ? "ماذا تريد أن تكتب؟"
                    : "ما الذي تريد البحث عنه؟";
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
       Conversation Memory
    ========================================================= */

    function getConversationHistory() {
        if (!state.memoryEnabled) {
            return [];
        }

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
            .filter(message => {

                const text =
                    String(
                        message.text ||
                        ""
                    ).trim();

                return (
                    text &&
                    (
                        message.type ===
                            "user" ||
                        message.type ===
                            "ai"
                    )
                );
            })
            .slice(-20)
            .map(message => ({
                type:
                    message.type,

                text:
                    String(
                        message.text
                    )
            }));
    }


    /* =========================================================
       Backend
    ========================================================= */

    async function sendMessage() {

        if (state.busy) return;

        const input =
            $("#message");

        if (!input) return;

        const text =
            input.value.trim();

        if (!text) return;

        if (!state.currentChatId) {
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
                "⏳ NORYN يعمل على طلبك...",
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
                                message: text,

                                mode:
                                    state.mode,

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

                let message =
                    "HTTP " +
                    response.status;

                try {

                    const errorData =
                        JSON.parse(raw);

                    message =
                        errorData.error ||
                        errorData.detail ||
                        message;

                } catch (_) {}

                throw new Error(
                    message
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
                "❌ حدث خطأ.\n\n" +
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

            send.classList.toggle(
                "loading",
                value
            );
        }

        if (input) {
            input.disabled =
                value;
        }
    }


    /* =========================================================
       History UI
    ========================================================= */

    function renderHistory() {
        const list =
            $("#historyList");

        if (!list) return;

        list.innerHTML = "";

        if (!state.chats.length) {

            const empty =
                document.createElement(
                    "div"
                );

            empty.className =
                "empty-history";

            empty.textContent =
                "لا توجد محادثات محفوظة.";

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


            const icon =
                chat.mode === "write"
                    ? "✍️"
                    : "🔎";


            open.textContent =
                icon +
                " " +
                (
                    chat.title ||
                    "محادثة"
                );


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
            "search"
        );

        renderChat(chat);

        closeAllPanels();

        const input =
            $("#message");

        if (input) {
            input.focus();
        }
    }


    /* =========================================================
       Panels
    ========================================================= */

    function openHistory() {
        closeSettings();

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


    function openSettings() {
        closeHistory();

        const panel =
            $("#settingsPanel");

        if (!panel) return;

        panel.classList.add(
            "open"
        );

        panel.setAttribute(
            "aria-hidden",
            "false"
        );
    }


    function closeSettings() {
        const panel =
            $("#settingsPanel");

        if (!panel) return;

        panel.classList.remove(
            "open"
        );

        panel.setAttribute(
            "aria-hidden",
            "true"
        );
    }


    function closeAllPanels() {
        closeHistory();
        closeSettings();
    }


    /* =========================================================
       Voice
    ========================================================= */

    function startVoice() {

        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (!SpeechRecognition) {

            showToast(
                "التعرف على الصوت غير مدعوم في هذا المتصفح."
            );

            return;
        }


        const recognition =
            new SpeechRecognition();

        recognition.lang =
            "ar-SA";

        recognition.interimResults =
            false;

        recognition.maxAlternatives =
            1;


        recognition.onstart = () => {
            showToast(
                "🎤 تحدث الآن..."
            );
        };


        recognition.onresult =
            event => {

                const result =
                    event.results[0][0]
                        .transcript;

                const input =
                    $("#message");

                if (input) {
                    input.value =
                        result;

                    input.focus();
                }
            };


        recognition.onerror =
            () => {

                showToast(
                    "تعذر استخدام الميكروفون."
                );
            };


        recognition.start();
    }


    /* =========================================================
       File Button
    ========================================================= */

    function attachFile() {

        const input =
            document.createElement(
                "input"
            );

        input.type =
            "file";

        input.accept =
            ".txt,.md,.html,.css,.js,.py,.json,.csv";


        input.addEventListener(
            "change",
            async () => {

                const file =
                    input.files[0];

                if (!file) return;


                if (
                    file.size >
                    1024 * 1024
                ) {
                    showToast(
                        "الملف كبير جدًا."
                    );

                    return;
                }


                try {

                    const text =
                        await file.text();

                    const message =
                        $("#message");

                    if (!message) return;


                    message.value =
                        `ملف: ${file.name}\n\n` +
                        text;

                    message.focus();


                    showToast(
                        "تمت إضافة الملف."
                    );

                } catch (error) {

                    console.error(
                        error
                    );

                    showToast(
                        "تعذر قراءة الملف."
                    );
                }
            }
        );


        input.click();
    }


    /* =========================================================
       Setup
    ========================================================= */

    function setup() {

        if (
            window.__NORYN_V7_INITIALIZED__
        ) {
            return;
        }

        window.__NORYN_V7_INITIALIZED__ =
            true;


        loadSettings();

        loadChats();


        /* Modes */

        $all("[data-mode]")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        setMode(
                            button.dataset.mode
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


        /* Input */

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


            input.addEventListener(
                "input",
                () => {

                    input.style.height =
                        "auto";

                    input.style.height =
                        Math.min(
                            input.scrollHeight,
                            180
                        ) + "px";
                }
            );
        }


        /* New Chat */

        const newChat =
            $("#newChat");

        if (newChat) {

            newChat.addEventListener(
                "click",
                createNewChat
            );
        }


        /* History */

        const historyButton =
            $("#historyButton");

        if (historyButton) {

            historyButton.addEventListener(
                "click",
                openHistory
            );
        }


        const closeHistoryButton =
            $("#closeHistory");

        if (closeHistoryButton) {

            closeHistoryButton.addEventListener(
                "click",
                closeHistory
            );
        }


        const panelNewChat =
            $("#panelNewChat");

        if (panelNewChat) {

            panelNewChat.addEventListener(
                "click",
                createNewChat
            );
        }


        /* Settings */

        const settingsButton =
            $("#settingsButton");

        if (settingsButton) {

            settingsButton.addEventListener(
                "click",
                openSettings
            );
        }


        const closeSettingsButton =
            $("#closeSettings");

        if (closeSettingsButton) {

            closeSettingsButton.addEventListener(
                "click",
                closeSettings
            );
        }


        /* Theme */

        const themeToggle =
            $("#themeToggle");

        if (themeToggle) {

            themeToggle.addEventListener(
                "click",
                () => {

                    state.darkMode =
                        !state.darkMode;

                    applyTheme();

                    saveSettings();

                    updateSettingsUI();
                }
            );
        }


        /* Temporary Chat */

        const temporaryToggle =
            $("#temporaryChatToggle");

        if (temporaryToggle) {

            temporaryToggle.addEventListener(
                "click",
                () => {

                    state.temporaryChat =
                        !state.temporaryChat;

                    saveSettings();

                    updateSettingsUI();

                    showToast(
                        state.temporaryChat
                            ? "تم تشغيل المحادثة المؤقتة."
                            : "تم إيقاف المحادثة المؤقتة."
                    );
                }
            );
        }


        /* Memory */

        const memoryToggle =
            $("#memoryToggle");

        if (memoryToggle) {

            memoryToggle.addEventListener(
                "click",
                () => {

                    state.memoryEnabled =
                        !state.memoryEnabled;

                    saveSettings();

                    updateSettingsUI();

                    showToast(
                        state.memoryEnabled
                            ? "تم تشغيل الذاكرة."
                            : "تم إيقاف الذاكرة."
                    );
                }
            );
        }


        /* Clear Chats */

        const clearChats =
            $("#clearChats");

        if (clearChats) {

            clearChats.addEventListener(
                "click",
                () => {

                    if (
                        !window.confirm(
                            "هل تريد حذف جميع المحادثات؟"
                        )
                    ) {
                        return;
                    }

                    state.chats = [];

                    state.currentChatId =
                        null;

                    localStorage.removeItem(
                        STORAGE_KEY
                    );

                    createNewChat();

                    showToast(
                        "تم حذف جميع المحادثات."
                    );
                }
            );
        }


        /* Voice */

        const voiceButton =
            $("#voiceButton");

        if (voiceButton) {

            voiceButton.addEventListener(
                "click",
                startVoice
            );
        }


        /* Attach */

        const attachButton =
            $("#attachButton");

        if (attachButton) {

            attachButton.addEventListener(
                "click",
                attachFile
            );
        }


        /* Suggestions */

        $all(".suggestion")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const inputBox =
                            $("#message");

                        if (!inputBox)
                            return;

                        inputBox.value =
                            button.dataset
                                .prompt ||
                            button.textContent
                                .trim();

                        inputBox.focus();
                    }
                );
            });


        /* Close panels by background */

        $all(".side-panel")
            .forEach(panel => {

                panel.addEventListener(
                    "click",
                    event => {

                        if (
                            event.target ===
                            panel
                        ) {
                            panel.classList.remove(
                                "open"
                            );
                        }
                    }
                );
            });


        /* Restore latest chat */

        if (state.chats.length) {

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
                "search"
            );

            renderChat(
                latest
            );

        } else {

            setMode("search");

            createNewChat();
        }


        renderHistory();

        updateSettingsUI();
    }


    /* =========================================================
       Initialization
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
