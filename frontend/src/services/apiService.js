const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000/api";

export function getFriendlyErrorMessage(error, fallback = "We’re having trouble reaching the service right now. Please try again in a moment.") {
    if (error instanceof Error && error.message) {
        const message = error.message.trim();
        if (!message) {
            return fallback;
        }

        if (
            /failed to fetch|networkerror|load failed|fetch failed|timed out|connection refused|socket hang up|econnreset/i.test(message)
        ) {
            return fallback;
        }

        return message;
    }

    return fallback;
}

async function request(endpoint, { method = "GET", body = null, headers = {}, isFormData = false } = {}) {
    const config = {
        method,
        headers: { ...headers },
    };

    if (body !== null) {
        config.body = body;
    }

    if (!isFormData && body !== null && !config.headers["Content-Type"]) {
        config.headers["Content-Type"] = "application/json";
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json")
            ? await response.json().catch(() => ({}))
            : await response.text();

        if (!response.ok) {
            const message = typeof data === "string"
                ? data
                : data?.error || `Request failed with status ${response.status}`;
            throw new Error(message);
        }

        return data;
    } catch (error) {
        if (error instanceof Error && error.message) {
            throw new Error(getFriendlyErrorMessage(error));
        }

        throw new Error(getFriendlyErrorMessage(null));
    }
}

export async function getApiStatus() {
    return request("/status");
}

export async function loginUser(credentials) {
    return request("/login", {
        method: "POST",
        body: JSON.stringify(credentials),
    });
}

export async function uploadReceipt(file, userId) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", userId);

    return request("/upload", {
        method: "POST",
        body: formData,
        isFormData: true,
    });
}

export async function getDashboardData(userId) {
    return request(`/dashboard?user_id=${encodeURIComponent(userId)}`);
}

export async function getUserReceipts(userId) {
    return request(`/receipts?user_id=${encodeURIComponent(userId)}`);
}

export async function clearAllData() {
    return request("/clear-data", {
        method: "POST",
    });
}

export { API_BASE_URL };
