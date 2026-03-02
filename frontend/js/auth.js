// ─── Auth Helpers ─────────────────────────────────────────────────────────────

function guardPage() {
    const token = localStorage.getItem("traffic_token");
    if (!token) {
        window.location.href = "/login.html";
    }
    // Populate nav user info
    try {
        const user = JSON.parse(localStorage.getItem("traffic_user") || "{}");
        const nameEl = document.getElementById("nav-username");
        const roleEl = document.getElementById("nav-role");
        const avatarEl = document.getElementById("avatar-initials");
        if (nameEl) nameEl.textContent = user.username || "Admin";
        if (roleEl) roleEl.textContent = user.role || "Admin";
        if (avatarEl) avatarEl.textContent = (user.username || "A").charAt(0).toUpperCase();
    } catch (e) { }
}

function logout() {
    localStorage.removeItem("traffic_token");
    localStorage.removeItem("traffic_user");
    window.location.href = "/login.html";
}
