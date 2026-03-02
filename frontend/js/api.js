// ─── API Wrapper ──────────────────────────────────────────────────────────────
// All fetch calls to the Flask backend live here.
const BASE = "http://localhost:5000/api";

function getToken() {
    return localStorage.getItem("traffic_token") || "";
}

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
    };
}

async function apiFetch(path, options = {}) {
    const res = await fetch(BASE + path, {
        headers: authHeaders(),
        ...options
    });
    if (res.status === 401) {
        localStorage.removeItem("traffic_token");
        localStorage.removeItem("traffic_user");
        window.location.href = "/login.html";
        return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "API error");
    return data;
}

const API = {
    // Auth
    login: (username, password) =>
        apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
    verify: () => apiFetch("/auth/verify"),
    logout: () => apiFetch("/auth/logout", { method: "POST" }),

    // Traffic
    trafficSnapshot: () => apiFetch("/traffic/snapshot"),
    trafficHistory: (limit = 20) => apiFetch(`/traffic/history?limit=${limit}`),

    // Signals
    currentSignal: () => apiFetch("/signals/current"),
    signalHistory: (limit = 20) => apiFetch(`/signals/history?limit=${limit}`),
    overrideSignal: (lane, duration) =>
        apiFetch("/signals/override", { method: "POST", body: JSON.stringify({ lane, duration }) }),

    // Violations
    violations: (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return apiFetch(`/violations/?${q}`);
    },
    violationDetail: (id) => apiFetch(`/violations/${id}`),

    // ANPR
    anprPlates: (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return apiFetch(`/anpr/?${q}`);
    },

    // Analytics
    analyticsSummary: () => apiFetch("/analytics/summary"),
    analyticsHourly: () => apiFetch("/analytics/hourly"),
    analyticsLanes: () => apiFetch("/analytics/lanes"),

    // Settings
    getSettings: () => apiFetch("/settings/"),
    updateSettings: (body) =>
        apiFetch("/settings/", { method: "PUT", body: JSON.stringify(body) })
};
