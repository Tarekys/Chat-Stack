(function () {
    const API_BASE_URL = window.CHATAPP_CONFIG.API_BASE_URL.replace(/\/$/, "");

    async function request(path, options = {}) {
        const {
            method = "GET",
            token = null,
            body = null,
            headers = {},
            form = false
        } = options;

        const requestHeaders = { ...headers };

        if (!form) {
            requestHeaders["Content-Type"] = "application/json";
        }

        if (token) {
            requestHeaders.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${path}`, {
            method,
            headers: requestHeaders,
            body: body
                ? form
                    ? body
                    : JSON.stringify(body)
                : null
        });

        const contentType = response.headers.get("content-type") || "";
        const payload = contentType.includes("application/json")
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message =
                typeof payload === "object" && payload !== null
                    ? payload.message || payload.detail || "Request failed"
                    : "Request failed";

            const error = new Error(message);
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    window.ChatStackAPI = {
        baseUrl: API_BASE_URL,
        signup(userData) {
            return request("/api/users/signup", {
                method: "POST",
                body: userData
            });
        },
        login(credentials) {
            return request("/api/users/login", {
                method: "POST",
                body: credentials
            });
        },
        requestPasswordReset(email) {
            return request("/api/auth/reset_password", {
                method: "POST",
                body: { email }
            });
        },
        confirmPasswordReset(token, passwords) {
            return request(`/api/auth/reset_password_confirm/${encodeURIComponent(token)}`, {
                method: "POST",
                body: passwords
            });
        },
        me(token) {
            return request("/api/users/me", {
                token
            });
        },
        logout(token) {
            return request("/api/users/logout", {
                token
            });
        },
        getConversations(token) {
            return request("/api/conversations/me", {
                token
            });
        },
        createConversation(token, payload) {
            return request("/api/conversations/", {
                method: "POST",
                token,
                body: payload
            });
        },
        updateConversation(token, conversationId, payload) {
            return request(`/api/conversations/${conversationId}`, {
                method: "PUT",
                token,
                body: payload
            });
        },
        deleteConversation(token, conversationId) {
            return request(`/api/conversations/${conversationId}`, {
                method: "DELETE",
                token
            });
        },
        getConversationMessages(conversationId) {
            return request(`/api/messages/conversation/${conversationId}`);
        },
        sendMessage(payload) {
            return request("/api/messages/", {
                method: "POST",
                body: payload
            });
        }
    };
})();
