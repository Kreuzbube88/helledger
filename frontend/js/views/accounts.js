import { api } from "../api.js";
import { renderNav } from "../nav.js";
import { navigate } from "../router.js";

export async function renderAccounts() {
    const app = document.getElementById("app");

    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-5xl mx-auto">',
        '    <div class="flex items-center justify-between mb-6">',
        '      <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '      <button id="btn-add" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"></button>',
        '    </div>',
        '    <div class="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">',
        '      <table class="w-full">',
        '        <thead class="border-b border-gray-800"><tr>',
        '          <th id="th-name" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-type" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-balance" class="text-right px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-currency" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-status" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th class="px-6 py-3"></th>',
        '        </tr></thead>',
        '        <tbody id="accounts-body" class="divide-y divide-gray-800"></tbody>',
        '      </table>',
        '    </div>',
        '  </main>',
        '</div>',
        '<div id="modal" class="hidden fixed inset-0 bg-black/60 flex items-center justify-center z-50">',
        '  <div class="bg-gray-900 rounded-2xl border border-gray-800 p-6 w-full max-w-md mx-4">',
        '    <h2 id="modal-title" class="text-lg font-semibold mb-4"></h2>',
        '    <form id="modal-form" class="space-y-4">',
        '      <div><label id="lbl-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-name" type="text" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-type" class="block text-sm text-gray-400 mb-1"></label>',
        '        <select id="modal-type" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <option id="opt-checking" value="checking"></option>',
        '          <option id="opt-savings" value="savings"></option>',
        '          <option id="opt-credit" value="credit"></option>',
        '        </select></div>',
        '      <div><label id="lbl-balance" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-balance" type="number" step="0.01" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-currency" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-currency" type="text" value="EUR" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div class="flex gap-3 pt-2">',
        '        <button type="submit" id="modal-save" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg transition-colors"></button>',
        '        <button type="button" id="modal-cancel" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg transition-colors"></button>',
        '      </div>',
        '    </form>',
        '  </div>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("accounts.title");
    document.getElementById("btn-add").textContent = t("accounts.add");
    document.getElementById("th-name").textContent = t("accounts.name");
    document.getElementById("th-type").textContent = t("accounts.type");
    document.getElementById("th-balance").textContent = t("accounts.balance");
    document.getElementById("th-currency").textContent = t("accounts.currency");
    document.getElementById("th-status").textContent = t("accounts.status");
    document.getElementById("lbl-name").textContent = t("accounts.name");
    document.getElementById("lbl-type").textContent = t("accounts.type");
    document.getElementById("lbl-balance").textContent = t("accounts.balance");
    document.getElementById("lbl-currency").textContent = t("accounts.currency");
    document.getElementById("modal-save").textContent = t("accounts.save");
    document.getElementById("modal-cancel").textContent = t("accounts.cancel");
    document.getElementById("opt-checking").textContent = t("accounts.types.checking");
    document.getElementById("opt-savings").textContent = t("accounts.types.savings");
    document.getElementById("opt-credit").textContent = t("accounts.types.credit");

    let editingId = null;

    async function loadAccounts() {
        const r = await api.get("/accounts");
        if (!r.ok) return;
        const accounts = await r.json();
        const tbody = document.getElementById("accounts-body");
        tbody.innerHTML = "";

        accounts.forEach((acc) => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-gray-800/50 transition-colors";

            const tdName = document.createElement("td");
            tdName.className = "px-6 py-4 text-sm font-medium text-white";
            tdName.textContent = acc.name;

            const tdType = document.createElement("td");
            tdType.className = "px-6 py-4 text-sm";
            const typeBadge = document.createElement("span");
            typeBadge.className = "px-2 py-0.5 rounded text-xs bg-indigo-900/50 text-indigo-300";
            typeBadge.textContent = t("accounts.types." + acc.account_type) || acc.account_type;
            tdType.appendChild(typeBadge);

            const tdBal = document.createElement("td");
            tdBal.className = "px-6 py-4 text-sm text-right font-mono text-gray-200";
            tdBal.textContent = parseFloat(acc.starting_balance).toLocaleString("de-DE", { minimumFractionDigits: 2 });

            const tdCur = document.createElement("td");
            tdCur.className = "px-6 py-4 text-sm text-gray-400";
            tdCur.textContent = acc.currency;

            const tdStatus = document.createElement("td");
            tdStatus.className = "px-6 py-4 text-sm";
            const statusBadge = document.createElement("span");
            statusBadge.className = acc.archived
                ? "px-2 py-0.5 rounded text-xs bg-red-900/40 text-red-400"
                : "px-2 py-0.5 rounded text-xs bg-green-900/40 text-green-400";
            statusBadge.textContent = acc.archived ? t("accounts.archived") : t("accounts.active");
            tdStatus.appendChild(statusBadge);

            const tdActions = document.createElement("td");
            tdActions.className = "px-6 py-4 text-sm";
            const actDiv = document.createElement("div");
            actDiv.className = "flex gap-3 justify-end";

            const editBtn = document.createElement("button");
            editBtn.className = "text-indigo-400 hover:text-indigo-300 transition-colors text-xs";
            editBtn.textContent = t("accounts.edit");
            editBtn.addEventListener("click", async () => {
                const res = await api.get("/accounts/" + acc.id);
                if (!res.ok) return;
                const data = await res.json();
                editingId = acc.id;
                document.getElementById("modal-name").value = data.name;
                document.getElementById("modal-type").value = data.account_type;
                document.getElementById("modal-balance").value = data.starting_balance;
                document.getElementById("modal-currency").value = data.currency;
                document.getElementById("modal-title").textContent = t("accounts.edit");
                document.getElementById("modal").classList.remove("hidden");
            });

            const archiveBtn = document.createElement("button");
            archiveBtn.className = "text-red-400 hover:text-red-300 transition-colors text-xs";
            archiveBtn.textContent = t("accounts.archive");
            archiveBtn.addEventListener("click", async () => {
                await api.delete("/accounts/" + acc.id);
                await loadAccounts();
            });

            actDiv.appendChild(editBtn);
            actDiv.appendChild(archiveBtn);
            tdActions.appendChild(actDiv);

            [tdName, tdType, tdBal, tdCur, tdStatus, tdActions].forEach((td) => tr.appendChild(td));
            tbody.appendChild(tr);
        });
    }

    document.getElementById("btn-add").addEventListener("click", () => {
        editingId = null;
        document.getElementById("modal-form").reset();
        document.getElementById("modal-currency").value = "EUR";
        document.getElementById("modal-title").textContent = t("accounts.add");
        document.getElementById("modal").classList.remove("hidden");
    });

    document.getElementById("modal-cancel").addEventListener("click", () => {
        document.getElementById("modal").classList.add("hidden");
    });

    document.getElementById("modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById("modal-name").value,
            account_type: document.getElementById("modal-type").value,
            starting_balance: document.getElementById("modal-balance").value,
            currency: document.getElementById("modal-currency").value,
        };
        if (editingId) {
            await api.patch("/accounts/" + editingId, payload);
        } else {
            await api.post("/accounts", payload);
        }
        document.getElementById("modal").classList.add("hidden");
        await loadAccounts();
    });

    await loadAccounts();
}
