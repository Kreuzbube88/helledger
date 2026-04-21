import { api } from "../api.js";
import { renderNav } from "../nav.js";

export async function renderSettings() {
    const app = document.getElementById("app");

    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-2xl mx-auto space-y-8">',
        '    <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '    <section class="bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4">',
        '      <h2 id="sec-household" class="text-lg font-semibold"></h2>',
        '      <div>',
        '        <label id="lbl-hh-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <div class="flex gap-3">',
        '          <input id="hh-name-input" type="text" class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <button id="btn-save-hh" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm"></button>',
        '        </div>',
        '      </div>',
        '    </section>',
        '    <section class="bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4">',
        '      <h2 id="sec-members" class="text-lg font-semibold"></h2>',
        '      <div id="members-list" class="space-y-2"></div>',
        '      <div class="flex gap-3 pt-2 border-t border-gray-800">',
        '        <input id="member-email" type="email" class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500">',
        '        <button id="btn-add-member" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm"></button>',
        '      </div>',
        '      <div id="member-error" class="hidden text-red-400 text-sm"></div>',
        '    </section>',
        '  </main>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("settings.title");
    document.getElementById("sec-household").textContent = t("settings.household");
    document.getElementById("lbl-hh-name").textContent = t("settings.householdName");
    document.getElementById("btn-save-hh").textContent = t("settings.save");
    document.getElementById("sec-members").textContent = t("settings.members");
    document.getElementById("btn-add-member").textContent = t("settings.add");
    document.getElementById("member-email").placeholder = t("settings.memberEmail");

    const meRes = await api.get("/auth/me");
    if (!meRes.ok) return;
    const user = await meRes.json();
    const hhId = user.active_household_id;
    if (!hhId) return;

    const hhsRes = await api.get("/households");
    const hhs = hhsRes.ok ? await hhsRes.json() : [];
    const hh = hhs.find((h) => h.id === hhId) || null;
    if (hh) document.getElementById("hh-name-input").value = hh.name;

    document.getElementById("btn-save-hh").addEventListener("click", async () => {
        const newName = document.getElementById("hh-name-input").value.trim();
        if (!newName) return;
        await api.patch("/households/" + hhId, { name: newName });
    });

    async function loadMembers() {
        const r = await api.get("/households/" + hhId + "/members");
        if (!r.ok) return;
        const members = await r.json();
        const list = document.getElementById("members-list");
        list.innerHTML = "";

        members.forEach((m) => {
            const row = document.createElement("div");
            row.className = "flex items-center justify-between py-2 px-3 bg-gray-800/40 rounded-lg";

            const info = document.createElement("div");
            info.className = "flex items-center gap-2 flex-1";
            const nameSpan = document.createElement("span");
            nameSpan.className = "text-sm text-white";
            nameSpan.textContent = m.name;
            const emailSpan = document.createElement("span");
            emailSpan.className = "text-xs text-gray-400";
            emailSpan.textContent = m.email;
            const roleSpan = document.createElement("span");
            roleSpan.className = "text-xs text-indigo-400";
            roleSpan.textContent = t("settings.roles." + m.role) || m.role;
            info.appendChild(nameSpan);
            info.appendChild(emailSpan);
            info.appendChild(roleSpan);

            row.appendChild(info);

            if (m.user_id !== user.id && hh && hh.owner_id === user.id) {
                const btn = document.createElement("button");
                btn.className = "text-xs text-red-400 hover:text-red-300 transition-colors";
                btn.textContent = t("settings.remove");
                btn.addEventListener("click", async () => {
                    await api.delete("/households/" + hhId + "/members/" + m.user_id);
                    await loadMembers();
                });
                row.appendChild(btn);
            }

            list.appendChild(row);
        });
    }

    document.getElementById("btn-add-member").addEventListener("click", async () => {
        const email = document.getElementById("member-email").value.trim();
        const errBox = document.getElementById("member-error");
        errBox.classList.add("hidden");
        if (!email) return;
        const r = await api.post("/households/" + hhId + "/members", { email });
        if (r.ok) {
            document.getElementById("member-email").value = "";
            await loadMembers();
        } else {
            const err = await r.json();
            errBox.textContent = err.detail || t("errors.generic");
            errBox.classList.remove("hidden");
        }
    });

    await loadMembers();
}
