import { api } from "../api.js";
import { renderNav } from "../nav.js";

export async function renderCategories() {
    const app = document.getElementById("app");

    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-4xl mx-auto">',
        '    <div class="flex items-center justify-between mb-6">',
        '      <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '      <button id="btn-add" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"></button>',
        '    </div>',
        '    <div id="cat-sections" class="space-y-8"></div>',
        '  </main>',
        '</div>',
        '<div id="cat-modal" class="hidden fixed inset-0 bg-black/60 flex items-center justify-center z-50">',
        '  <div class="bg-gray-900 rounded-2xl border border-gray-800 p-6 w-full max-w-md mx-4">',
        '    <h2 id="cat-modal-title" class="text-lg font-semibold mb-4"></h2>',
        '    <form id="cat-modal-form" class="space-y-4">',
        '      <div><label id="lbl-cat-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="cat-name" type="text" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-cat-type" class="block text-sm text-gray-400 mb-1"></label>',
        '        <select id="cat-type" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <option id="opt-income" value="income"></option>',
        '          <option id="opt-fixed" value="fixed"></option>',
        '          <option id="opt-variable" value="variable"></option>',
        '        </select></div>',
        '      <div><label id="lbl-cat-color" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="cat-color" type="color" value="#6366f1" class="h-10 w-full rounded-lg bg-gray-800 border border-gray-700 cursor-pointer"></div>',
        '      <input id="cat-parent-id" type="hidden" value="">',
        '      <div class="flex gap-3 pt-2">',
        '        <button type="submit" id="cat-save" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg transition-colors"></button>',
        '        <button type="button" id="cat-cancel" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg transition-colors"></button>',
        '      </div>',
        '    </form>',
        '  </div>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("categories.title");
    document.getElementById("btn-add").textContent = t("categories.add");
    document.getElementById("lbl-cat-name").textContent = t("categories.name");
    document.getElementById("lbl-cat-type").textContent = t("categories.type");
    document.getElementById("lbl-cat-color").textContent = t("categories.color");
    document.getElementById("opt-income").textContent = t("categories.types.income");
    document.getElementById("opt-fixed").textContent = t("categories.types.fixed");
    document.getElementById("opt-variable").textContent = t("categories.types.variable");
    document.getElementById("cat-save").textContent = t("categories.save");
    document.getElementById("cat-cancel").textContent = t("categories.cancel");

    let editingCatId = null;

    function openModal(title, parentId, existing) {
        editingCatId = existing ? existing.id : null;
        document.getElementById("cat-modal-title").textContent = title;
        document.getElementById("cat-name").value = existing ? existing.name : "";
        document.getElementById("cat-type").value = existing ? existing.category_type : "fixed";
        document.getElementById("cat-color").value = existing && existing.color ? existing.color : "#6366f1";
        document.getElementById("cat-parent-id").value = parentId != null ? parentId : "";
        document.getElementById("cat-modal").classList.remove("hidden");
    }

    document.getElementById("cat-cancel").addEventListener("click", () => {
        document.getElementById("cat-modal").classList.add("hidden");
    });

    document.getElementById("cat-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const parentRaw = document.getElementById("cat-parent-id").value;
        const payload = {
            name: document.getElementById("cat-name").value,
            category_type: document.getElementById("cat-type").value,
            color: document.getElementById("cat-color").value,
            parent_id: parentRaw !== "" ? parseInt(parentRaw, 10) : null,
        };
        if (editingCatId) {
            await api.patch("/categories/" + editingCatId, payload);
        } else {
            await api.post("/categories", payload);
        }
        document.getElementById("cat-modal").classList.add("hidden");
        await loadCategories();
    });

    document.getElementById("btn-add").addEventListener("click", () => {
        openModal(t("categories.add"), null, null);
    });

    async function loadEvPanel(catId, panel, isVariable) {
        const endpoint = isVariable ? "/budgets" : "/expected-values";
        const r = await api.get(endpoint + "?category_id=" + catId);
        if (!r.ok) return;
        const items = await r.json();
        panel.innerHTML = "";

        items.forEach((item) => {
            const row = document.createElement("div");
            row.className = "flex items-center justify-between py-1 text-sm";
            const span = document.createElement("span");
            span.className = "text-gray-300";
            const until = item.valid_until || t("categories.noLimit");
            span.textContent = item.amount + " \u20AC \u00B7 " + item.valid_from + " \u2192 " + until;
            const del = document.createElement("button");
            del.className = "text-red-400 hover:text-red-300 text-xs ml-2";
            del.textContent = "\u00D7";
            del.addEventListener("click", async () => {
                await api.delete(endpoint + "/" + item.id);
                await loadEvPanel(catId, panel, isVariable);
            });
            row.appendChild(span);
            row.appendChild(del);
            panel.appendChild(row);
        });

        const form = document.createElement("form");
        form.className = "flex gap-2 mt-2";
        const amtIn = document.createElement("input");
        amtIn.type = "number";
        amtIn.step = "0.01";
        amtIn.placeholder = t("categories.amount");
        amtIn.className = "flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white";
        const dateIn = document.createElement("input");
        dateIn.type = "date";
        dateIn.placeholder = t("categories.validFrom");
        dateIn.className = "flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white";
        const btn = document.createElement("button");
        btn.type = "submit";
        btn.className = "bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1 rounded";
        btn.textContent = isVariable ? t("categories.newBudget") : t("categories.newExpectedValue");
        form.appendChild(amtIn);
        form.appendChild(dateIn);
        form.appendChild(btn);
        form.addEventListener("submit", async (ev) => {
            ev.preventDefault();
            if (!amtIn.value || !dateIn.value) return;
            await api.post(endpoint, {
                category_id: catId,
                amount: amtIn.value,
                valid_from: dateIn.value,
            });
            await loadEvPanel(catId, panel, isVariable);
        });
        panel.appendChild(form);
    }

    function buildCategoryRow(cat, depth) {
        const wrapper = document.createElement("div");

        wrapper.innerHTML = [
            '<div class="cat-row flex items-center gap-3 py-2 px-4 hover:bg-gray-800/40 rounded-lg">',
            '  <span class="color-dot w-3 h-3 rounded-full flex-shrink-0"></span>',
            '  <span class="cat-name flex-1 text-sm text-white"></span>',
            '  <div class="flex gap-2">',
            '    <button class="btn-ev text-xs text-gray-400 hover:text-indigo-400 transition-colors"></button>',
            '    <button class="btn-sub text-xs text-gray-400 hover:text-green-400 transition-colors"></button>',
            '    <button class="btn-edit text-xs text-gray-400 hover:text-white transition-colors"></button>',
            '    <button class="btn-arc text-xs text-red-400/60 hover:text-red-400 transition-colors"></button>',
            '  </div>',
            '</div>',
            '<div class="ev-panel hidden px-4 pb-3 bg-gray-800/20 rounded-lg mx-2 mb-1"></div>',
        ].join("\n");

        wrapper.querySelector(".cat-row").style.paddingLeft = (16 + depth * 24) + "px";
        wrapper.querySelector(".color-dot").style.backgroundColor = cat.color || "#6366f1";
        wrapper.querySelector(".cat-name").textContent = cat.name;

        const isVariable = cat.category_type === "variable";
        wrapper.querySelector(".btn-ev").textContent = isVariable ? t("categories.budget") : t("categories.expectedValue");
        wrapper.querySelector(".btn-sub").textContent = t("categories.addSub");
        wrapper.querySelector(".btn-edit").textContent = t("categories.edit");
        wrapper.querySelector(".btn-arc").textContent = t("categories.archive");

        const evPanel = wrapper.querySelector(".ev-panel");

        wrapper.querySelector(".btn-ev").addEventListener("click", async () => {
            evPanel.classList.toggle("hidden");
            if (!evPanel.classList.contains("hidden")) {
                await loadEvPanel(cat.id, evPanel, isVariable);
            }
        });
        wrapper.querySelector(".btn-sub").addEventListener("click", () => openModal(t("categories.addSub"), cat.id, null));
        wrapper.querySelector(".btn-edit").addEventListener("click", () => openModal(t("categories.edit"), cat.parent_id, cat));
        wrapper.querySelector(".btn-arc").addEventListener("click", async () => {
            await api.delete("/categories/" + cat.id);
            await loadCategories();
        });

        return wrapper;
    }

    function renderTree(nodes, container, depth) {
        nodes.forEach((cat) => {
            container.appendChild(buildCategoryRow(cat, depth));
            if (cat.children && cat.children.length > 0) {
                renderTree(cat.children, container, depth + 1);
            }
        });
    }

    async function loadCategories() {
        const r = await api.get("/categories");
        if (!r.ok) return;
        const tree = await r.json();
        const sections = document.getElementById("cat-sections");
        sections.innerHTML = "";

        ["income", "fixed", "variable"].forEach((catType) => {
            const nodes = tree.filter((n) => n.category_type === catType);
            if (nodes.length === 0) return;
            const section = document.createElement("div");
            const heading = document.createElement("h2");
            heading.className = "text-lg font-semibold text-gray-300 mb-3";
            heading.textContent = t("categories.sections." + catType);
            section.appendChild(heading);
            const card = document.createElement("div");
            card.className = "bg-gray-900 rounded-2xl border border-gray-800 py-2";
            renderTree(nodes, card, 0);
            section.appendChild(card);
            sections.appendChild(section);
        });
    }

    await loadCategories();
}
