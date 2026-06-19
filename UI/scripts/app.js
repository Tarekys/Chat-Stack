(function () {
    const STORAGE_KEYS = {
        accessToken: "chatstack.accessToken",
        refreshToken: "chatstack.refreshToken",
        userData: "chatstack.userData"
    };

    const state = {
        accessToken: localStorage.getItem(STORAGE_KEYS.accessToken) || "",
        refreshToken: localStorage.getItem(STORAGE_KEYS.refreshToken) || "",
        user: readStoredJson(STORAGE_KEYS.userData),
        conversations: [],
        filteredConversations: [],
        activeConversation: null,
        messages: []
    };

    const elements = {
        authScreen: document.getElementById("authScreen"),
        verificationScreen: document.getElementById("verificationScreen"),
        chatScreen: document.getElementById("chatScreen"),
        authMessage: document.getElementById("authMessage"),
        chatMessage: document.getElementById("chatMessage"),
        loginForm: document.getElementById("loginForm"),
        signupForm: document.getElementById("signupForm"),
        verifiedGoLogin: document.getElementById("verifiedGoLogin"),
        openResendPage: document.getElementById("openResendPage"),
        composerForm: document.getElementById("composerForm"),
        messageInput: document.getElementById("messageInput"),
        conversationList: document.getElementById("conversationList"),
        conversationSearch: document.getElementById("conversationSearch"),
        messagesContainer: document.getElementById("messagesContainer"),
        emptyState: document.getElementById("emptyState"),
        newChatButton: document.getElementById("newChatButton"),
        logoutButton: document.getElementById("logoutButton"),
        sidebarUsername: document.getElementById("sidebarUsername"),
        sidebarEmail: document.getElementById("sidebarEmail"),
        userAvatar: document.getElementById("userAvatar"),
        verificationHint: document.getElementById("verificationHint"),
        chatTitle: document.getElementById("chatTitle"),
        chatSubtitle: document.getElementById("chatSubtitle")
    };

    init();

    async function init() {
        bindEvents();

        if (state.accessToken) {
            try {
                const me = await window.ChatStackAPI.me(state.accessToken);
                state.user = me;
                persistUserOnly();
                showChatScreen();
                hydrateSidebarUser();
                await loadConversations();
                return;
            } catch (error) {
                clearSession();
            }
        }

        showAuthScreen();
    }

    function bindEvents() {
        document.querySelectorAll("[data-auth-tab]").forEach((button) => {
            button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
        });

        elements.loginForm.addEventListener("submit", onLoginSubmit);
        elements.signupForm.addEventListener("submit", onSignupSubmit);
        elements.verifiedGoLogin.addEventListener("click", () => {
            switchAuthTab("login");
            showAuthScreen();
        });
        elements.openResendPage.addEventListener("click", () => {
            window.open(`${window.ChatStackAPI.baseUrl}/api/users/resend-verification`, "_blank");
        });
        elements.newChatButton.addEventListener("click", onNewChat);
        elements.logoutButton.addEventListener("click", onLogout);
        elements.composerForm.addEventListener("submit", onComposerSubmit);
        elements.conversationSearch.addEventListener("input", onConversationSearch);
        elements.messageInput.addEventListener("input", autoResizeComposer);

        // Close any open conv-menu when clicking outside
        document.addEventListener("click", (e) => {
            if (!e.target.closest(".conversation-item__actions")) {
                closeAllMenus();
            }
        });
    }

    function closeAllMenus() {
        document.querySelectorAll(".conv-menu-dropdown").forEach((d) => d.remove());
        document.querySelectorAll(".conv-menu-trigger.is-active").forEach((t) => t.classList.remove("is-active"));
        document.querySelectorAll(".conversation-item__actions.is-open").forEach((a) => a.classList.remove("is-open"));
    }

    function switchAuthTab(tabName) {
        const isLogin = tabName === "login";
        document.querySelectorAll("[data-auth-tab]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.authTab === tabName);
        });
        elements.loginForm.classList.toggle("is-hidden", !isLogin);
        elements.signupForm.classList.toggle("is-hidden", isLogin);
        clearBox(elements.authMessage);
    }

    async function onLoginSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);

        const formData = new FormData(elements.loginForm);
        const payload = Object.fromEntries(formData.entries());

        try {
            setFormBusy(elements.loginForm, true);
            const response = await window.ChatStackAPI.login(payload);

            state.accessToken = response.access_token;
            state.refreshToken = response.refresh_token || "";
            state.user = await window.ChatStackAPI.me(state.accessToken);

            persistSession();
            showChatScreen();
            hydrateSidebarUser();
            await loadConversations();
            elements.loginForm.reset();
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.loginForm, false);
        }
    }

    async function onSignupSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);

        const formData = new FormData(elements.signupForm);
        const payload = Object.fromEntries(formData.entries());

        try {
            setFormBusy(elements.signupForm, true);
            await window.ChatStackAPI.signup(payload);
            elements.signupForm.reset();
            elements.verificationHint.textContent =
                `We sent a verification link to ${payload.email}. Open your email, click the verification link, then come back and log in.`;
            showVerificationScreen();
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.signupForm, false);
        }
    }

    async function onLogout() {
        try {
            if (state.accessToken) {
                await window.ChatStackAPI.logout(state.accessToken);
            }
        } catch (error) {
            // Ignore logout transport errors and clear local session anyway.
        } finally {
            clearSession();
            resetChatState();
            showAuthScreen();
        }
    }

    async function onNewChat() {
        try {
            clearBox(elements.chatMessage);
            const conversation = await createConversationForUser("New chat");
            await setActiveConversation(conversation.id);
            elements.messageInput.focus();
        } catch (error) {
            showBox(elements.chatMessage, error.message, "error");
        }
    }

    async function onComposerSubmit(event) {
        event.preventDefault();
        clearBox(elements.chatMessage);

        const content = elements.messageInput.value.trim();
        if (!content) {
            return;
        }

        try {
            setComposerBusy(true);

            if (!state.activeConversation) {
                const title = buildConversationTitle(content);
                const conversation = await createConversationForUser(title);
                await setActiveConversation(conversation.id);
            }

            appendLocalMessage("user", content);
            appendLocalLoading();
            elements.messageInput.value = "";
            autoResizeComposer();

            const assistantMessage = await window.ChatStackAPI.sendMessage({
                conversation_id: state.activeConversation.id,
                content
            });

            removeLoadingMessage();
            state.messages.push(assistantMessage);
            renderMessages();
            await loadConversations(false);
        } catch (error) {
            removeLoadingMessage();
            showBox(elements.chatMessage, error.message, "error");
        } finally {
            setComposerBusy(false);
        }
    }

    function onConversationSearch() {
        const query = elements.conversationSearch.value.trim().toLowerCase();
        state.filteredConversations = state.conversations.filter((conversation) =>
            (conversation.title || "Untitled chat").toLowerCase().includes(query)
        );
        renderConversations();
    }

    async function loadConversations(selectLatest = true) {
        if (!state.accessToken || !state.user) {
            return;
        }

        const conversations = await window.ChatStackAPI.getConversations(state.accessToken);
        const sortedConversations = conversations
            .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));

        state.conversations = sortedConversations;
        state.filteredConversations = sortedConversations;
        renderConversations();

        if (selectLatest && sortedConversations.length > 0) {
            await setActiveConversation(sortedConversations[0].id);
        } else if (sortedConversations.length === 0) {
            state.activeConversation = null;
            state.messages = [];
            renderMessages();
        }
    }

    async function setActiveConversation(conversationId) {
        const conversation = state.conversations.find((item) => item.id === conversationId);
        if (!conversation) {
            return;
        }

        state.activeConversation = conversation;
        state.messages = await window.ChatStackAPI.getConversationMessages(conversationId);
        renderConversations();
        renderMessages();
        updateChatHeader();
    }

    async function createConversationForUser(title) {
        const userId = state.user.user_id || state.user.id;
        const conversation = await window.ChatStackAPI.createConversation(state.accessToken, {
            title,
            user_id: userId
        });

        state.conversations = [conversation, ...state.conversations];
        state.filteredConversations = [conversation, ...state.filteredConversations];
        return conversation;
    }

    async function onRenameConversation(conversationId) {
        const conversation = state.conversations.find((item) => item.id === conversationId);
        if (!conversation) {
            return;
        }

        const nextTitle = window.prompt("Enter a new conversation title", conversation.title || "");
        if (nextTitle === null) {
            return;
        }

        const normalizedTitle = nextTitle.trim();
        if (!normalizedTitle) {
            showBox(elements.chatMessage, "Conversation title cannot be empty.", "error");
            return;
        }

        try {
            clearBox(elements.chatMessage);
            const updatedConversation = await window.ChatStackAPI.updateConversation(
                state.accessToken,
                conversationId,
                { title: normalizedTitle }
            );

            replaceConversationInState(updatedConversation);
            if (state.activeConversation && state.activeConversation.id === conversationId) {
                state.activeConversation = updatedConversation;
                updateChatHeader();
            }
            renderConversations();
            showBox(elements.chatMessage, "Conversation updated successfully.", "success");
        } catch (error) {
            showBox(elements.chatMessage, error.message, "error");
        }
    }

    async function onDeleteConversation(conversationId) {
        const conversation = state.conversations.find((item) => item.id === conversationId);
        if (!conversation) {
            return;
        }

        const confirmed = window.confirm(`Delete conversation "${conversation.title || "Untitled chat"}"?`);
        if (!confirmed) {
            return;
        }

        try {
            clearBox(elements.chatMessage);
            await window.ChatStackAPI.deleteConversation(state.accessToken, conversationId);

            removeConversationFromState(conversationId);

            if (state.activeConversation && state.activeConversation.id === conversationId) {
                if (state.conversations.length > 0) {
                    await setActiveConversation(state.conversations[0].id);
                } else {
                    state.activeConversation = null;
                    state.messages = [];
                    renderMessages();
                }
            } else {
                renderConversations();
            }

            showBox(elements.chatMessage, "Conversation deleted successfully.", "success");
        } catch (error) {
            showBox(elements.chatMessage, error.message, "error");
        }
    }

    function replaceConversationInState(updatedConversation) {
        state.conversations = state.conversations.map((conversation) =>
            conversation.id === updatedConversation.id ? updatedConversation : conversation
        );
        state.filteredConversations = state.filteredConversations.map((conversation) =>
            conversation.id === updatedConversation.id ? updatedConversation : conversation
        );
    }

    function removeConversationFromState(conversationId) {
        state.conversations = state.conversations.filter((conversation) => conversation.id !== conversationId);
        state.filteredConversations = state.filteredConversations.filter((conversation) => conversation.id !== conversationId);
    }

    function renderConversations() {
        const list = state.filteredConversations;
        elements.conversationList.innerHTML = "";

        if (!list.length) {
            const empty = document.createElement("div");
            empty.className = "status-box";
            empty.textContent = "No conversations yet.";
            elements.conversationList.appendChild(empty);
            return;
        }

        list.forEach((conversation) => {
            const item = document.createElement("div");
            item.className = `conversation-item${state.activeConversation && state.activeConversation.id === conversation.id ? " is-active" : ""}`;

            // ── Main clickable area ──
            const button = document.createElement("button");
            button.type = "button";
            button.className = "conversation-item__main";
            button.innerHTML = `
                <strong>${escapeHtml(conversation.title || "Untitled chat")}</strong>
                <span>${formatDate(conversation.updated_at || conversation.created_at)}</span>
            `;
            button.addEventListener("click", async () => {
                closeAllMenus();
                await setActiveConversation(conversation.id);
            });

            // ── 3-dot trigger ──
            const actions = document.createElement("div");
            actions.className = "conversation-item__actions";

            const trigger = document.createElement("button");
            trigger.type = "button";
            trigger.className = "conv-menu-trigger";
            trigger.title = "More options";
            trigger.setAttribute("aria-label", "More options");
            trigger.innerHTML = `<span style="font-size:18px;letter-spacing:-1px;line-height:1">&#8942;</span>`;

            trigger.addEventListener("click", (event) => {
                event.stopPropagation();

                const isAlreadyOpen = trigger.classList.contains("is-active");
                closeAllMenus();
                if (isAlreadyOpen) return;

                // Build dropdown
                const dropdown = document.createElement("div");
                dropdown.className = "conv-menu-dropdown";

                const renameItem = document.createElement("button");
                renameItem.type = "button";
                renameItem.className = "conv-menu-item";
                renameItem.innerHTML = `<span class="conv-menu-item__icon">&#9998;</span> Rename`;
                renameItem.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    closeAllMenus();
                    await onRenameConversation(conversation.id);
                });

                const separator = document.createElement("div");
                separator.className = "conv-menu-separator";

                const deleteItem = document.createElement("button");
                deleteItem.type = "button";
                deleteItem.className = "conv-menu-item conv-menu-item--danger";
                deleteItem.innerHTML = `<span class="conv-menu-item__icon">&#128465;</span> Delete`;
                deleteItem.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    closeAllMenus();
                    await onDeleteConversation(conversation.id);
                });

                dropdown.append(renameItem, separator, deleteItem);

                // Position dropdown using fixed coords so it never clips
                const rect = trigger.getBoundingClientRect();
                dropdown.style.top  = `${rect.bottom + 6}px`;
                dropdown.style.left = `${rect.left - 140}px`;
                document.body.appendChild(dropdown);

                trigger.classList.add("is-active");
                actions.classList.add("is-open");
            });

            actions.appendChild(trigger);
            item.append(button, actions);
            elements.conversationList.appendChild(item);
        });
    }

    function renderMessages() {
        elements.messagesContainer.innerHTML = "";
        updateChatHeader();

        if (!state.messages.length) {
            elements.messagesContainer.appendChild(elements.emptyState);
            return;
        }

        state.messages.forEach((message) => {
            const row = document.createElement("div");
            row.className = `message-row message-row--${message.role}`;

            const bubble = document.createElement("div");
            bubble.className = "message-bubble";
            bubble.textContent = message.content;

            row.appendChild(bubble);
            elements.messagesContainer.appendChild(row);
        });

        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    function appendLocalMessage(role, content) {
        state.messages.push({ role, content });
        renderMessages();
    }

    function appendLocalLoading() {
        state.messages.push({
            role: "assistant",
            content: "Thinking",
            isLoading: true
        });
        renderMessages();

        const lastBubble = elements.messagesContainer.querySelector(".message-row:last-child .message-bubble");
        if (lastBubble) {
            lastBubble.classList.add("loading-dots");
        }
    }

    function removeLoadingMessage() {
        if (state.messages.length && state.messages[state.messages.length - 1].isLoading) {
            state.messages.pop();
        }
        renderMessages();
    }

    function updateChatHeader() {
        if (state.activeConversation) {
            elements.chatTitle.textContent = state.activeConversation.title || "Conversation";
            elements.chatSubtitle.textContent = "Continue your conversation with the assistant.";
        } else {
            elements.chatTitle.textContent = "What’s on your mind today?";
            elements.chatSubtitle.textContent = "Start a new conversation or continue an existing one.";
        }
    }

    function hydrateSidebarUser() {
        if (!state.user) {
            return;
        }

        const username = state.user.username || state.user.email || "User";
        const email = state.user.email || "";

        elements.sidebarUsername.textContent = username;
        elements.sidebarEmail.textContent = email;
        elements.userAvatar.textContent = username.charAt(0).toUpperCase();
    }

    function showAuthScreen() {
        elements.authScreen.classList.remove("is-hidden");
        elements.verificationScreen.classList.add("is-hidden");
        elements.chatScreen.classList.add("is-hidden");
    }

    function showVerificationScreen() {
        elements.authScreen.classList.add("is-hidden");
        elements.verificationScreen.classList.remove("is-hidden");
        elements.chatScreen.classList.add("is-hidden");
    }

    function showChatScreen() {
        elements.authScreen.classList.add("is-hidden");
        elements.verificationScreen.classList.add("is-hidden");
        elements.chatScreen.classList.remove("is-hidden");
    }

    function setFormBusy(form, busy) {
        form.querySelectorAll("input, button").forEach((element) => {
            element.disabled = busy;
        });
    }

    function setComposerBusy(busy) {
        elements.messageInput.disabled = busy;
        document.getElementById("sendButton").disabled = busy;
    }

    function autoResizeComposer() {
        const textarea = elements.messageInput;
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
    }

    function showBox(target, text, kind) {
        target.textContent = text;
        target.classList.remove("is-hidden", "is-error", "is-success");
        target.classList.add(kind === "error" ? "is-error" : "is-success");
    }

    function clearBox(target) {
        target.textContent = "";
        target.classList.add("is-hidden");
        target.classList.remove("is-error", "is-success");
    }

    function buildConversationTitle(content) {
        const normalized = content.replace(/\s+/g, " ").trim();
        return normalized.length > 32 ? `${normalized.slice(0, 32)}...` : normalized;
    }

    function formatDate(value) {
        if (!value) {
            return "Just now";
        }
        return new Date(value).toLocaleString();
    }

    function clearSession() {
        state.accessToken = "";
        state.refreshToken = "";
        state.user = null;
        localStorage.removeItem(STORAGE_KEYS.accessToken);
        localStorage.removeItem(STORAGE_KEYS.refreshToken);
        localStorage.removeItem(STORAGE_KEYS.userData);
    }

    function persistSession() {
        localStorage.setItem(STORAGE_KEYS.accessToken, state.accessToken);
        localStorage.setItem(STORAGE_KEYS.refreshToken, state.refreshToken);
        localStorage.setItem(STORAGE_KEYS.userData, JSON.stringify(state.user));
    }

    function persistUserOnly() {
        localStorage.setItem(STORAGE_KEYS.userData, JSON.stringify(state.user));
    }

    function resetChatState() {
        state.conversations = [];
        state.filteredConversations = [];
        state.activeConversation = null;
        state.messages = [];
        elements.conversationList.innerHTML = "";
        elements.messageInput.value = "";
        elements.conversationSearch.value = "";
        renderMessages();
        clearBox(elements.chatMessage);
    }

    function readStoredJson(key) {
        const rawValue = localStorage.getItem(key);
        if (!rawValue) {
            return null;
        }

        try {
            return JSON.parse(rawValue);
        } catch (error) {
            localStorage.removeItem(key);
            return null;
        }
    }

    function escapeHtml(value) {
        return value
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }
})();
