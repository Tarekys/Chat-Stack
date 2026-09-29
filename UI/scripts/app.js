(function () {
    const STORAGE_KEYS = {
        accessToken: "chatstack.accessToken",
        refreshToken: "chatstack.refreshToken",
        userData: "chatstack.userData"
    };

    // ─── State ───────────────────────────────────────
    const state = {
        accessToken: localStorage.getItem(STORAGE_KEYS.accessToken) || "",
        refreshToken: localStorage.getItem(STORAGE_KEYS.refreshToken) || "",
        user: readStoredJson(STORAGE_KEYS.userData),
        conversations: [],
        filteredConversations: [],
        activeConversation: null,
        messages: [],
        passwordResetToken: "",
        pendingImages: [],
        lastLoginEmail: ""
    };

    // ─── DOM References ───────────────────────────────
    const elements = {
        authScreen: document.getElementById("authScreen"),
        verificationScreen: document.getElementById("verificationScreen"),
        chatScreen: document.getElementById("chatScreen"),
        authMessage: document.getElementById("authMessage"),
        chatMessage: document.getElementById("chatMessage"),
        loginForm: document.getElementById("loginForm"),
        signupForm: document.getElementById("signupForm"),
        authTabs: document.querySelector(".auth-tabs"),
        authEyebrow: document.getElementById("authEyebrow"),
        authTitle: document.getElementById("authTitle"),
        forgotPasswordButton: document.getElementById("forgotPasswordButton"),
        resendVerificationBtnLogin: document.getElementById("resendVerificationBtnLogin"),
        passwordResetRequestForm: document.getElementById("passwordResetRequestForm"),
        passwordResetConfirmForm: document.getElementById("passwordResetConfirmForm"),
        verifiedGoLogin: document.getElementById("verifiedGoLogin"),
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
        chatSubtitle: document.getElementById("chatSubtitle"),
        imageFileInput: document.getElementById("imageFileInput"),
        attachImageBtn: document.getElementById("attachImageBtn"),
        imagePreviewStrip: document.getElementById("imagePreviewStrip"),
        sendButton: document.getElementById("sendButton"),
        imageLightbox: document.getElementById("imageLightbox"),
        lightboxImage: document.getElementById("lightboxImage"),
        closeLightboxBtn: document.getElementById("closeLightboxBtn")
    };

    init();

    // ─── Init ─────────────────────────────────────────
    async function init() {
        bindEvents();

        const resetToken = new URLSearchParams(window.location.search).get("reset_token");
        if (resetToken) {
            state.passwordResetToken = resetToken;
            showAuthScreen();
            showPasswordRecovery("confirm");
            return;
        }

        if (state.accessToken) {
            try {
                const me = await window.ChatStackAPI.me(state.accessToken);
                state.user = me;
                persistUserOnly();
                showChatScreen();
                hydrateSidebarUser();
                await loadConversations(false);
                return;
            } catch (error) {
                // Only clear session on auth errors (401), not network failures
                if (error.status === 401 || error.status === 403) {
                    clearSession();
                } else {
                    // Network error or server down — keep token, show chat with cached data
                    if (state.user) {
                        showChatScreen();
                        hydrateSidebarUser();
                        showBox(elements.chatMessage, "Connection issue. Some features may be unavailable.", "error");
                        return;
                    }
                    clearSession();
                }
            }
        }

        showAuthScreen();
    }

    // ─── Event Binding ────────────────────────────────
    function bindEvents() {
        document.querySelectorAll("[data-auth-tab]").forEach((button) => {
            button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
        });

        elements.loginForm.addEventListener("submit", onLoginSubmit);
        elements.signupForm.addEventListener("submit", onSignupSubmit);
        elements.forgotPasswordButton.addEventListener("click", () => showPasswordRecovery("request"));
        elements.passwordResetRequestForm.addEventListener("submit", onPasswordResetRequestSubmit);
        elements.passwordResetConfirmForm.addEventListener("submit", onPasswordResetConfirmSubmit);

        document.querySelectorAll("[data-return-login]").forEach((button) => {
            button.addEventListener("click", () => switchAuthTab("login"));
        });

        elements.verifiedGoLogin.addEventListener("click", () => {
            switchAuthTab("login");
            showAuthScreen();
        });

        elements.resendVerificationBtnLogin.addEventListener("click", onResendVerificationLoginClick);

        elements.newChatButton.addEventListener("click", onNewChat);
        elements.logoutButton.addEventListener("click", onLogout);
        elements.composerForm.addEventListener("submit", onComposerSubmit);
        elements.conversationSearch.addEventListener("input", onConversationSearch);

        elements.messageInput.addEventListener("input", autoResizeComposer);
        elements.messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                elements.composerForm.requestSubmit();
            }
        });

        // Image attach
        elements.attachImageBtn.addEventListener("click", () => elements.imageFileInput.click());
        elements.imageFileInput.addEventListener("change", onImageFilesSelected);

        // Drag & drop onto the composer
        elements.composerForm.addEventListener("dragover", (e) => { e.preventDefault(); });
        elements.composerForm.addEventListener("drop", (e) => {
            e.preventDefault();
            const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith("image/"));
            if (files.length) addImagesToQueue(files);
        });

        // Lightbox closing
        elements.closeLightboxBtn.addEventListener("click", closeLightbox);
        elements.imageLightbox.addEventListener("click", (e) => {
            if (e.target === elements.imageLightbox) closeLightbox();
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") closeLightbox();
        });

        // Close menus
        document.addEventListener("click", (e) => {
            if (!e.target.closest(".conversation-item__actions")) closeAllMenus();
        });
    }

    // ─── Image Queue ──────────────────────────────────
    function onImageFilesSelected() {
        const files = Array.from(elements.imageFileInput.files).filter((f) => f.type.startsWith("image/"));
        addImagesToQueue(files);
        elements.imageFileInput.value = "";
    }

    function addImagesToQueue(files) {
        files.forEach((file) => {
            const previewUrl = URL.createObjectURL(file);
            state.pendingImages.push({ file, previewUrl });
        });
        renderImagePreview();
    }

    function removeImageFromQueue(index) {
        URL.revokeObjectURL(state.pendingImages[index].previewUrl);
        state.pendingImages.splice(index, 1);
        renderImagePreview();
    }

    function clearImageQueue() {
        state.pendingImages.forEach((img) => URL.revokeObjectURL(img.previewUrl));
        state.pendingImages = [];
        renderImagePreview();
    }

    function renderImagePreview() {
        const strip = elements.imagePreviewStrip;
        strip.innerHTML = "";

        if (!state.pendingImages.length) {
            strip.classList.add("is-hidden");
            elements.attachImageBtn.classList.remove("has-images");
            return;
        }

        strip.classList.remove("is-hidden");
        elements.attachImageBtn.classList.add("has-images");

        state.pendingImages.forEach((img, index) => {
            const item = document.createElement("div");
            item.className = "image-preview-item";

            const imgEl = document.createElement("img");
            imgEl.src = img.previewUrl;
            imgEl.alt = img.file.name;

            const removeBtn = document.createElement("button");
            removeBtn.className = "image-preview-remove";
            removeBtn.type = "button";
            removeBtn.title = "Remove image";
            removeBtn.textContent = "✕";
            removeBtn.addEventListener("click", () => removeImageFromQueue(index));

            item.append(imgEl, removeBtn);
            strip.appendChild(item);
        });
    }

    // ─── Auth ─────────────────────────────────────────
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
        elements.authTabs.classList.remove("is-hidden");
        elements.loginForm.classList.toggle("is-hidden", !isLogin);
        elements.signupForm.classList.toggle("is-hidden", isLogin);
        elements.passwordResetRequestForm.classList.add("is-hidden");
        elements.passwordResetConfirmForm.classList.add("is-hidden");
        elements.resendVerificationBtnLogin.classList.add("is-hidden");
        elements.authEyebrow.textContent = "Welcome back";
        elements.authTitle.textContent = "Log in or sign up";
        clearBox(elements.authMessage);
    }

    function showPasswordRecovery(mode) {
        elements.authTabs.classList.add("is-hidden");
        elements.loginForm.classList.add("is-hidden");
        elements.signupForm.classList.add("is-hidden");
        elements.passwordResetRequestForm.classList.toggle("is-hidden", mode !== "request");
        elements.passwordResetConfirmForm.classList.toggle("is-hidden", mode !== "confirm");
        elements.authEyebrow.textContent = "Account recovery";
        elements.authTitle.textContent = mode === "confirm" ? "Choose a new password" : "Forgot password?";
        clearBox(elements.authMessage);
    }

    async function onPasswordResetRequestSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);
        const formData = new FormData(elements.passwordResetRequestForm);
        try {
            setFormBusy(elements.passwordResetRequestForm, true);
            const response = await window.ChatStackAPI.requestPasswordReset(formData.get("email"));
            showBox(elements.authMessage, response.message || "Check your email for a reset link.", "success");
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.passwordResetRequestForm, false);
        }
    }

    async function onPasswordResetConfirmSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);
        const formData = new FormData(elements.passwordResetConfirmForm);
        const passwords = Object.fromEntries(formData.entries());
        try {
            setFormBusy(elements.passwordResetConfirmForm, true);
            const response = await window.ChatStackAPI.confirmPasswordReset(state.passwordResetToken, passwords);
            state.passwordResetToken = "";
            window.history.replaceState({}, document.title, window.location.pathname);
            switchAuthTab("login");
            showBox(elements.authMessage, response.message || "Password updated. You can now log in.", "success");
            elements.passwordResetConfirmForm.reset();
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.passwordResetConfirmForm, false);
        }
    }

    async function onLoginSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);
        const payload = Object.fromEntries(new FormData(elements.loginForm).entries());
        try {
            setFormBusy(elements.loginForm, true);
            const response = await window.ChatStackAPI.login(payload);
            state.accessToken = response.access_token;
            state.refreshToken = response.refresh_token || "";
            state.user = await window.ChatStackAPI.me(state.accessToken);
            persistSession();
            showChatScreen();
            hydrateSidebarUser();
            await loadConversations(false);
            elements.loginForm.reset();
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
            if (error.message.toLowerCase().includes("not verified")) {
                state.lastLoginEmail = payload.email;
                elements.resendVerificationBtnLogin.classList.remove("is-hidden");
            } else {
                elements.resendVerificationBtnLogin.classList.add("is-hidden");
            }
        } finally {
            setFormBusy(elements.loginForm, false);
        }
    }

    async function onResendVerificationLoginClick() {
        if (!state.lastLoginEmail) return;
        try {
            setFormBusy(elements.loginForm, true);
            await window.ChatStackAPI.resendVerification(state.lastLoginEmail);
            showBox(elements.authMessage, "Verification email sent. Please check your inbox.", "success");
            elements.resendVerificationBtnLogin.classList.add("is-hidden");
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.loginForm, false);
        }
    }

    async function onSignupSubmit(event) {
        event.preventDefault();
        clearBox(elements.authMessage);
        const payload = Object.fromEntries(new FormData(elements.signupForm).entries());
        try {
            setFormBusy(elements.signupForm, true);
            await window.ChatStackAPI.signup(payload);
            elements.signupForm.reset();
            elements.verificationHint.textContent =
                `We sent a verification link to ${payload.email}. Click it, then come back and log in.`;
            showVerificationScreen();
        } catch (error) {
            showBox(elements.authMessage, error.message, "error");
        } finally {
            setFormBusy(elements.signupForm, false);
        }
    }

    async function onLogout() {
        try {
            if (state.accessToken) await window.ChatStackAPI.logout(state.accessToken);
        } catch (_) { /* ignore */ } finally {
            clearSession();
            resetChatState();
            showAuthScreen();
        }
    }

    // ─── Conversations ────────────────────────────────
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

    function onConversationSearch() {
        const query = elements.conversationSearch.value.trim().toLowerCase();
        state.filteredConversations = state.conversations.filter((c) =>
            (c.title || "Untitled chat").toLowerCase().includes(query)
        );
        renderConversations();
    }

    async function loadConversations(selectLatest = true) {
        if (!state.accessToken || !state.user) return;
        const conversations = await window.ChatStackAPI.getConversations(state.accessToken);
        const sorted = conversations.sort(
            (a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)
        );
        state.conversations = sorted;
        state.filteredConversations = sorted;
        renderConversations();

        if (selectLatest && sorted.length > 0) {
            await setActiveConversation(sorted[0].id);
        } else if (!state.activeConversation) {
            state.activeConversation = null;
            state.messages = [];
            renderMessages();
        }
    }

    async function setActiveConversation(conversationId) {
        const conversation = state.conversations.find((c) => c.id === conversationId);
        if (!conversation) return;
        state.activeConversation = conversation;
        state.messages = await window.ChatStackAPI.getConversationMessages(state.accessToken, conversationId);
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
        const conversation = state.conversations.find((c) => c.id === conversationId);
        if (!conversation) return;
        const nextTitle = window.prompt("Enter a new conversation title", conversation.title || "");
        if (nextTitle === null) return;
        const normalized = nextTitle.trim();
        if (!normalized) { showBox(elements.chatMessage, "Title cannot be empty.", "error"); return; }
        try {
            clearBox(elements.chatMessage);
            const updated = await window.ChatStackAPI.updateConversation(state.accessToken, conversationId, { title: normalized });
            replaceConversationInState(updated);
            if (state.activeConversation && state.activeConversation.id === conversationId) {
                state.activeConversation = updated;
                updateChatHeader();
            }
            renderConversations();
        } catch (error) {
            showBox(elements.chatMessage, error.message, "error");
        }
    }

    async function onDeleteConversation(conversationId) {
        const conversation = state.conversations.find((c) => c.id === conversationId);
        if (!conversation) return;
        if (!window.confirm(`Delete "${conversation.title || "Untitled chat"}"?`)) return;
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
                    updateChatHeader();
                }
            } else {
                renderConversations();
            }
        } catch (error) {
            showBox(elements.chatMessage, error.message, "error");
        }
    }

    // ─── Message Sending ──────────────────────────────
    async function onComposerSubmit(event) {
        event.preventDefault();
        clearBox(elements.chatMessage);

        const content = elements.messageInput.value.trim();
        const hasImages = state.pendingImages.length > 0;

        if (!content && !hasImages) return;

        try {
            setComposerBusy(true);

            // Auto-create conversation if none active
            if (!state.activeConversation) {
                const title = buildConversationTitle(content || "Image message");
                const conversation = await createConversationForUser(title);
                await setActiveConversation(conversation.id);
            }

            // Snapshot pending images for this send
            const imagesToSend = [...state.pendingImages];
            const previewUrls = imagesToSend.map((img) => img.previewUrl);

            // Clear composer
            elements.messageInput.value = "";
            autoResizeComposer();
            clearImageQueue();

            // Optimistic user message
            appendLocalMessage("user", content || "", previewUrls);
            appendLocalLoading();

            // 1. Upload images to S3 (parallel)
            let image_urls = [];
            if (imagesToSend.length > 0) {
                const uploadResults = await Promise.all(
                    imagesToSend.map((img) => window.ChatStackAPI.uploadImage(state.accessToken, img.file))
                );
                image_urls = uploadResults.map((r) => r.url);
            }

            // 2. Send message to AI
            const assistantMessage = await window.ChatStackAPI.sendMessage(state.accessToken, {
                conversation_id: state.activeConversation.id,
                content: content || " ",
                image_urls: image_urls.length > 0 ? image_urls : undefined
            });

            removeLoadingMessage();

            // Replace the optimistic user message (which used blob previewUrls)
            // with real S3 URLs so images don't break after the blob is revoked
            if (image_urls.length > 0) {
                const userMsgIndex = state.messages.findLastIndex(
                    (m) => m.role === "user" && m._previewUrls && m._previewUrls.length > 0
                );
                if (userMsgIndex !== -1) {
                    state.messages[userMsgIndex] = {
                        ...state.messages[userMsgIndex],
                        image_urls: image_urls,
                        _previewUrls: undefined
                    };
                }
            }

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

    // ─── Render ───────────────────────────────────────
    function renderConversations() {
        const list = state.filteredConversations;
        elements.conversationList.innerHTML = "";

        if (!list.length) {
            const empty = document.createElement("div");
            empty.className = "status-box";
            empty.style.fontSize = "13px";
            empty.textContent = "No conversations yet.";
            elements.conversationList.appendChild(empty);
            return;
        }

        list.forEach((conversation) => {
            const item = document.createElement("div");
            item.className = `conversation-item${state.activeConversation && state.activeConversation.id === conversation.id ? " is-active" : ""}`;

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

                const rect = trigger.getBoundingClientRect();
                dropdown.style.top = `${rect.bottom + 6}px`;
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

            // Show images if present
            const urls = message.image_urls || message._previewUrls;
            if (urls && urls.length > 0) {
                const imagesDiv = document.createElement("div");
                imagesDiv.className = "message-images";
                urls.forEach((url) => {
                    const img = document.createElement("img");
                    img.src = url;
                    img.className = "message-image";
                    img.alt = "Attached image";
                    img.referrerPolicy = "no-referrer";
                    img.addEventListener("click", () => openLightbox(url));
                    img.onerror = () => {
                        img.style.display = "none";
                        const errSpan = document.createElement("span");
                        errSpan.className = "image-load-error";
                        errSpan.textContent = "⚠ Image unavailable";
                        imagesDiv.appendChild(errSpan);
                    };
                    imagesDiv.appendChild(img);
                });
                bubble.appendChild(imagesDiv);
            }

            if (message.content && message.content.trim()) {
                const textNode = document.createElement("div");
                textNode.className = "message-text";
                textNode.innerHTML = renderMarkdown(message.content);
                bubble.appendChild(textNode);
            }

            if (message.isLoading) {
                bubble.classList.add("loading-dots");
            }

            row.appendChild(bubble);
            elements.messagesContainer.appendChild(row);
        });

        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    function appendLocalMessage(role, content, previewUrls = []) {
        state.messages.push({ role, content, _previewUrls: previewUrls });
        renderMessages();
    }

    function appendLocalLoading() {
        state.messages.push({ role: "assistant", content: "Thinking", isLoading: true });
        renderMessages();
        const lastBubble = elements.messagesContainer.querySelector(".message-row:last-child .message-bubble");
        if (lastBubble) lastBubble.classList.add("loading-dots");
    }

    function removeLoadingMessage() {
        if (state.messages.length && state.messages[state.messages.length - 1].isLoading) {
            state.messages.pop();
        }
        renderMessages();
    }

    // ─── Header ───────────────────────────────────────
    function updateChatHeader() {
        const header = document.querySelector(".chat-header");
        if (state.activeConversation && state.messages.length > 0) {
            elements.chatTitle.textContent = state.activeConversation.title || "Conversation";
            elements.chatSubtitle.textContent = "";
            header.classList.add("is-compact");
        } else if (state.activeConversation) {
            elements.chatTitle.textContent = state.activeConversation.title || "New conversation";
            elements.chatSubtitle.textContent = "Send a message to get started.";
            header.classList.remove("is-compact");
        } else {
            elements.chatTitle.textContent = "Where should we begin?";
            elements.chatSubtitle.textContent = "Start a new conversation or continue an existing one.";
            header.classList.remove("is-compact");
        }
    }

    // ─── Lightbox ─────────────────────────────────────
    function openLightbox(url) {
        elements.lightboxImage.referrerPolicy = "no-referrer";
        elements.lightboxImage.src = url;
        elements.imageLightbox.classList.remove("is-hidden");
    }

    function closeLightbox() {
        elements.imageLightbox.classList.add("is-hidden");
        setTimeout(() => { elements.lightboxImage.src = ""; }, 200);
    }

    // ─── Sidebar ──────────────────────────────────────
    function hydrateSidebarUser() {
        if (!state.user) return;
        const username = state.user.username || state.user.email || "User";
        const email = state.user.email || "";
        elements.sidebarUsername.textContent = username;
        elements.sidebarEmail.textContent = email;
        elements.userAvatar.textContent = username.charAt(0).toUpperCase();
    }

    // ─── Screens ──────────────────────────────────────
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

    // ─── Composer Helpers ─────────────────────────────
    function setFormBusy(form, busy) {
        form.querySelectorAll("input, button").forEach((el) => { el.disabled = busy; });
    }

    function setComposerBusy(busy) {
        elements.messageInput.disabled = busy;
        elements.sendButton.disabled = busy;
        elements.attachImageBtn.disabled = busy;
    }

    function autoResizeComposer() {
        const ta = elements.messageInput;
        ta.style.height = "auto";
        ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
    }

    // ─── State Helpers ────────────────────────────────
    function replaceConversationInState(updated) {
        state.conversations = state.conversations.map((c) => c.id === updated.id ? updated : c);
        state.filteredConversations = state.filteredConversations.map((c) => c.id === updated.id ? updated : c);
    }

    function removeConversationFromState(conversationId) {
        state.conversations = state.conversations.filter((c) => c.id !== conversationId);
        state.filteredConversations = state.filteredConversations.filter((c) => c.id !== conversationId);
    }

    // ─── UI Helpers ───────────────────────────────────
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
        return normalized.length > 36 ? `${normalized.slice(0, 36)}...` : normalized;
    }

    function formatDate(value) {
        if (!value) return "Just now";
        const d = new Date(value);
        const now = new Date();
        const diff = now - d;
        if (diff < 60000) return "Just now";
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return d.toLocaleDateString();
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
        clearImageQueue();
        elements.conversationList.innerHTML = "";
        elements.messageInput.value = "";
        elements.conversationSearch.value = "";
        renderMessages();
        clearBox(elements.chatMessage);
        updateChatHeader();
    }

    function readStoredJson(key) {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        try { return JSON.parse(raw); } catch { localStorage.removeItem(key); return null; }
    }

    function escapeHtml(value) {
        return value
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function renderMarkdown(text) {
        // Escape HTML first
        let escaped = escapeHtml(text);
        // Code blocks ```...```
        escaped = escaped.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
        // Inline code `...`
        escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");
        // Bold **...**
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        // Italic *...*
        escaped = escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");
        // Line breaks
        escaped = escaped.replace(/\n/g, "<br>");
        return escaped;
    }
})();
