import { logout } from "./auth.js";
import { api } from "./api.js";
import { navigate } from "./router.js";

function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === "className") node.className = v;
        else node.setAttribute(k, v);
    }
    for (const child of children) {
        if (typeof child === "string") node.appendChild(document.createTextNode(child));
        else if (child) node.appendChild(child);
    }
    return node;
}

function svgChevron() {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "w-3 h-3 flex-shrink-0");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("viewBox", "0 0 24 24");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("d", "M19 9l-7 7-7-7");
    svg.appendChild(path);
    return svg;
}

export async function renderNav(container) {
    const [hhRes, meRes] = await Promise.all([
        api.get("/households"),
        api.get("/auth/me"),
    ]);
    const households = hhRes.ok ? await hhRes.json() : [];
    const user = meRes.ok ? await meRes.json() : null;
    const activeHhId = user ? user.active_household_id : null;
    const activeHh = households.find((h) => h.id === activeHhId) || null;

    // Nav links
    const hash = window.location.hash;
    const pages = ["dashboard", "accounts", "categories", "transactions", "reports", "import", "settings"];
    if (user && user.role === "admin") pages.push("backup");
    const navLinks = pages.map((page) => {
        const isActive = hash === "#/" + page || hash.startsWith("#/" + page + "/");
        const a = el("a", {
            id: "nav-" + page,
            href: "#/" + page,
            className: "text-sm transition-colors " + (isActive ? "text-white font-medium" : "text-gray-400 hover:text-white"),
        });
        a.textContent = t("nav." + page);
        return a;
    });

    const nav = el("nav", { className: "flex gap-4" }, ...navLinks);

    const brand = el("span", { id: "nav-brand", className: "font-bold text-lg text-indigo-400" });
    brand.textContent = t("app.name");

    const left = el("div", { className: "flex items-center gap-6" }, brand, nav);

    // Household name span
    const hhNameSpan = el("span", { id: "hh-name", className: "max-w-32 truncate" });
    hhNameSpan.textContent = activeHh ? activeHh.name : "";

    // Household dropdown list
    const hhListDiv = el("div", { id: "hh-list" });
    households.forEach((hh) => {
        const btn = el("button", {
            className: "w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors " + (hh.id === activeHhId ? "text-indigo-400" : "text-gray-300"),
        });
        btn.textContent = hh.name;
        btn.addEventListener("click", async () => {
            await api.post("/households/" + hh.id + "/activate", {});
            location.reload();
        });
        hhListDiv.appendChild(btn);
    });

    const hhDropdown = el("div", {
        id: "hh-dropdown",
        className: "hidden absolute right-0 mt-2 w-52 bg-gray-800 rounded-lg border border-gray-700 shadow-xl z-50 py-1",
    }, hhListDiv);

    const hhToggle = el("button", {
        id: "hh-toggle",
        className: "flex items-center gap-1 text-sm text-gray-300 hover:text-white",
    }, hhNameSpan, svgChevron());

    const hhWrapper = el("div", { className: "relative" }, hhToggle, hhDropdown);

    // User name span
    const userSpan = el("span", { id: "nav-user", className: "text-sm text-gray-400" });
    if (user) userSpan.textContent = user.name;

    // Logout button
    const logoutBtn = el("button", {
        id: "nav-logout",
        className: "text-sm text-gray-400 hover:text-white transition-colors",
    });
    logoutBtn.textContent = t("nav.logout");

    const right = el("div", { className: "flex items-center gap-4" }, hhWrapper, userSpan, logoutBtn);

    const header = el("header", {
        className: "bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between",
    }, left, right);

    container.textContent = "";
    container.appendChild(header);

    // Event listeners
    hhToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        hhDropdown.classList.toggle("hidden");
    });
    document.addEventListener("click", () => {
        const dd = document.getElementById("hh-dropdown");
        if (dd) dd.classList.add("hidden");
    });

    logoutBtn.addEventListener("click", async () => {
        await logout();
        navigate("#/login");
    });
}
