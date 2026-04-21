import { api, getToken } from "../api.js";
import { renderNav } from "../nav.js";
import { toast } from "../toast.js";
import { navigate } from "../router.js";

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

export async function renderBackup() {
    const meRes = await api.get("/auth/me");
    if (!meRes.ok) { navigate("#/login"); return; }
    const user = await meRes.json();
    if (user.role !== "admin") { navigate("#/dashboard"); return; }

    const app = document.getElementById("app");
    app.textContent = "";

    const wrapper = el("div", "min-h-screen bg-gray-950 text-white");

    const navWrap = el("div");
    navWrap.id = "nav-container";
    wrapper.appendChild(navWrap);

    const main = el("main", "p-8 max-w-3xl mx-auto space-y-8");

    const title = el("h1", "text-2xl font-bold", t("backup.title"));
    main.appendChild(title);

    // Settings section
    const secSettings = el("section", "bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4");
    secSettings.appendChild(el("h2", "text-lg font-semibold", t("backup.settings")));
    const label = el("label", "block text-sm text-gray-400 mb-1", t("backup.retentionDays"));
    label.htmlFor = "retention-input";
    const row = el("div", "flex gap-3 items-center");
    const retInput = el("input", "w-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 text-sm");
    retInput.id = "retention-input";
    retInput.type = "number";
    retInput.min = "1";
    const saveBtn = el("button", "bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm", t("backup.save"));
    row.appendChild(retInput);
    row.appendChild(saveBtn);
    secSettings.appendChild(label);
    secSettings.appendChild(row);
    main.appendChild(secSettings);

    // Trigger section
    const secTrigger = el("section", "bg-gray-900 rounded-2xl border border-gray-800 p-6");
    const triggerBtn = el("button", "bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm", t("backup.triggerBtn"));
    secTrigger.appendChild(triggerBtn);
    main.appendChild(secTrigger);

    // List section
    const secList = el("section", "bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4");
    secList.appendChild(el("h2", "text-lg font-semibold", t("backup.list")));
    const listContainer = el("div");
    listContainer.id = "backup-list";
    secList.appendChild(listContainer);
    main.appendChild(secList);

    wrapper.appendChild(main);
    app.appendChild(wrapper);

    await renderNav(navWrap);

    // Load retention setting
    const sRes = await api.get("/backup/settings");
    if (sRes.ok) {
        const s = await sRes.json();
        retInput.value = s.backup_retention_days;
    }

    saveBtn.addEventListener("click", async () => {
        const days = parseInt(retInput.value, 10);
        if (!days || days < 1) return;
        const r = await api.patch("/backup/settings", { backup_retention_days: days });
        if (r.ok) toast(t("backup.saved"));
        else toast(t("errors.generic"), "error");
    });

    triggerBtn.addEventListener("click", async () => {
        const r = await api.post("/backup/trigger", {});
        if (r.ok) {
            toast(t("backup.triggerSuccess"));
            await _loadList();
        } else {
            toast(t("errors.generic"), "error");
        }
    });

    async function _loadList() {
        const r = await api.get("/backup/list");
        if (!r.ok) return;
        const items = await r.json();
        listContainer.textContent = "";

        if (!items.length) {
            listContainer.appendChild(el("p", "text-sm text-gray-500", t("backup.empty")));
            return;
        }

        const table = document.createElement("table");
        table.className = "w-full text-sm";

        const thead = document.createElement("thead");
        const hr = document.createElement("tr");
        hr.className = "text-left text-gray-400 border-b border-gray-800";
        [t("backup.filename"), t("backup.size"), t("backup.createdAt"), ""].forEach((text) => {
            const th = el("th", "pb-2 font-medium pr-4", text);
            hr.appendChild(th);
        });
        thead.appendChild(hr);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        items.forEach((item) => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-gray-800/50";

            const nameTd = el("td", "py-3 pr-4 font-mono text-xs text-gray-300", item.filename);
            const sizeTd = el("td", "py-3 pr-4 text-gray-400", (item.size_bytes / 1024).toFixed(1) + " KB");
            const dateTd = el("td", "py-3 pr-4 text-gray-400", new Date(item.created_at).toLocaleString());
            const actionsTd = el("td", "py-3 flex gap-3 justify-end");

            const dlBtn = el("button", "text-xs text-indigo-400 hover:text-indigo-300 transition-colors", t("backup.download"));
            dlBtn.addEventListener("click", async () => {
                const res = await fetch(`/api/backup/${item.filename}/download`, {
                    headers: { Authorization: `Bearer ${getToken()}` },
                });
                if (!res.ok) { toast(t("errors.generic"), "error"); return; }
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = item.filename;
                a.click();
                URL.revokeObjectURL(url);
            });

            const delBtn = el("button", "text-xs text-red-400 hover:text-red-300 transition-colors", t("backup.delete"));
            delBtn.addEventListener("click", async () => {
                if (!confirm(t("backup.deleteConfirm"))) return;
                const res = await api.delete(`/backup/${item.filename}`);
                if (res.ok) await _loadList();
                else toast(t("errors.generic"), "error");
            });

            actionsTd.appendChild(dlBtn);
            actionsTd.appendChild(delBtn);
            tr.appendChild(nameTd);
            tr.appendChild(sizeTd);
            tr.appendChild(dateTd);
            tr.appendChild(actionsTd);
            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        listContainer.appendChild(table);
    }

    await _loadList();
}
