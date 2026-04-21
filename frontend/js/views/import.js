import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api, getToken } from "../api.js";
import { toast } from "../toast.js";
import { fadeInUp } from "../animations.js";

let _step = 1;
let _parsed = null;
let _selectedFile = null;
let _accountId = null;
let _accounts = [];
let _categories = [];

export async function renderImport() {
    const user = await getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    const app = document.getElementById("app");
    app.textContent = "";

    const navWrap = document.createElement("div");
    app.appendChild(navWrap);
    await renderNav(navWrap);

    const main = document.createElement("main");
    main.className = "max-w-3xl mx-auto px-4 py-8";
    app.appendChild(main);

    if (!user.active_household_id) {
        const msg = document.createElement("div");
        msg.className = "glass rounded-2xl p-8 text-center text-gray-400";
        msg.textContent = t("import.noHousehold");
        main.appendChild(msg);
        return;
    }

    const [accRes, catRes] = await Promise.all([
        api.get("/accounts"),
        api.get("/categories"),
    ]);
    _accounts = accRes.ok ? (await accRes.json()).filter(a => !a.archived) : [];
    _categories = catRes.ok ? _flatCats(await catRes.json()) : [];

    _step = 1;
    _parsed = null;
    _selectedFile = null;
    _accountId = null;
    _render(main);
    fadeInUp(main);
}

function _flatCats(list) {
    const result = [];
    function walk(items) {
        items.forEach(c => { result.push(c); if (c.children) walk(c.children); });
    }
    walk(list);
    return result;
}

function _render(container) {
    container.textContent = "";

    const title = document.createElement("h1");
    title.className = "text-2xl font-bold text-white mb-6";
    title.textContent = t("import.title");
    container.appendChild(title);

    const steps = [t("import.step.upload"), t("import.step.mapping"), t("import.step.result")];
    const stepRow = document.createElement("div");
    stepRow.className = "flex items-center gap-2 mb-8";
    steps.forEach((label, i) => {
        const num = i + 1;
        const active = num === _step;
        const done = num < _step;
        const dot = document.createElement("div");
        dot.className = `w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
            done ? "bg-emerald-500 text-white" : active ? "bg-indigo-500 text-white" : "bg-gray-700 text-gray-400"
        }`;
        dot.textContent = done ? "✓" : String(num);
        const lbl = document.createElement("span");
        lbl.className = `text-sm ${active ? "text-white" : "text-gray-500"}`;
        lbl.textContent = label;
        stepRow.appendChild(dot);
        stepRow.appendChild(lbl);
        if (i < steps.length - 1) {
            const line = document.createElement("div");
            line.className = "flex-1 h-px bg-gray-700";
            stepRow.appendChild(line);
        }
    });
    container.appendChild(stepRow);

    const card = document.createElement("div");
    card.className = "glass rounded-2xl p-6";
    container.appendChild(card);

    if (_step === 1) _renderStep1(card);
    else if (_step === 2) _renderStep2(card);
    else _renderStep3(card);
}

function _label(text) {
    const el = document.createElement("label");
    el.className = "block text-sm text-gray-400 mb-1";
    el.textContent = text;
    return el;
}

function _select(options, value) {
    const sel = document.createElement("select");
    sel.className = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm";
    options.forEach(([val, label]) => {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        if (val === value) opt.selected = true;
        sel.appendChild(opt);
    });
    return sel;
}

function _renderStep1(card) {
    const accWrap = document.createElement("div");
    accWrap.className = "mb-4";
    accWrap.appendChild(_label(t("import.account")));
    const accSel = _select(_accounts.map(a => [String(a.id), a.name]), _accounts[0] ? String(_accounts[0].id) : "");
    accSel.id = "import-account";
    accWrap.appendChild(accSel);
    card.appendChild(accWrap);

    const dropzone = document.createElement("div");
    dropzone.id = "import-dropzone";
    dropzone.className = "border-2 border-dashed border-gray-600 rounded-xl p-10 text-center cursor-pointer hover:border-indigo-500 transition-colors mb-4";
    const dzLabel = document.createElement("div");
    dzLabel.id = "dropzone-label";
    dzLabel.className = "text-gray-300 text-sm mt-2";
    dzLabel.textContent = t("import.dropzone");
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.id = "import-file";
    fileInput.accept = ".csv,.ofx,.qfx";
    fileInput.className = "hidden";
    dropzone.appendChild(dzLabel);
    dropzone.appendChild(fileInput);
    card.appendChild(dropzone);

    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("border-indigo-500"); });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-indigo-500"));
    dropzone.addEventListener("drop", e => {
        e.preventDefault();
        dropzone.classList.remove("border-indigo-500");
        const file = e.dataTransfer?.files[0];
        if (file) _setFile(file, dzLabel);
    });
    fileInput.addEventListener("change", e => {
        const file = e.target.files?.[0];
        if (file) _setFile(file, dzLabel);
    });

    const btn = document.createElement("button");
    btn.id = "import-parse-btn";
    btn.className = "w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
    btn.textContent = t("import.step.upload");
    btn.disabled = true;
    btn.addEventListener("click", () => _doUpload(btn));
    card.appendChild(btn);
}

function _setFile(file, labelEl) {
    _selectedFile = file;
    if (labelEl) labelEl.textContent = file.name;
    const btn = document.getElementById("import-parse-btn");
    if (btn) btn.disabled = false;
}

async function _doUpload(btn) {
    if (!_selectedFile) return;
    btn.disabled = true;
    btn.textContent = "…";

    _accountId = document.getElementById("import-account")?.value || "";
    const formData = new FormData();
    formData.append("file", _selectedFile);
    formData.append("account_id", _accountId);

    const r = await fetch("/api/import/parse", {
        method: "POST",
        headers: { "Authorization": `Bearer ${getToken()}` },
        body: formData,
    });

    if (!r.ok) {
        toast(t("import.error.parseError"), "error");
        btn.disabled = false;
        btn.textContent = t("import.step.upload");
        return;
    }

    _parsed = await r.json();
    const main = document.querySelector("main");

    if (_parsed.format !== "csv") {
        _step = 3;
        _render(main);
        await _doConfirm(document.querySelector(".glass"));
    } else {
        _step = 2;
        _render(main);
    }
}

function _renderStep2(card) {
    if (!_parsed) return;

    const previewWrap = document.createElement("div");
    previewWrap.className = "overflow-x-auto mb-6";
    const table = document.createElement("table");
    table.className = "w-full text-xs text-gray-300";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    _parsed.columns.forEach(col => {
        const th = document.createElement("th");
        th.className = "px-2 py-1 text-left text-gray-500 font-medium";
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    _parsed.preview_rows.forEach(row => {
        const tr = document.createElement("tr");
        row.forEach(cell => {
            const td = document.createElement("td");
            td.className = "px-2 py-1 border-t border-gray-800 truncate max-w-32";
            td.textContent = cell;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    previewWrap.appendChild(table);
    card.appendChild(previewWrap);

    const colOptions = _parsed.columns.map(c => [c, c]);
    [
        ["date", t("import.field.date")],
        ["amount", t("import.field.amount")],
        ["description", t("import.field.description")],
    ].forEach(([key, label]) => {
        const wrap = document.createElement("div");
        wrap.className = "mb-3";
        wrap.appendChild(_label(label));
        const sel = _select(colOptions, _parsed.suggested_mapping[key] || _parsed.columns[0]);
        sel.id = `map-${key}`;
        wrap.appendChild(sel);
        card.appendChild(wrap);
    });

    const fmtWrap = document.createElement("div");
    fmtWrap.className = "mb-3";
    fmtWrap.appendChild(_label(t("import.field.dateFormat")));
    const fmtInput = document.createElement("input");
    fmtInput.id = "map-date-format";
    fmtInput.type = "text";
    fmtInput.value = _parsed.detected_date_format;
    fmtInput.className = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm";
    fmtWrap.appendChild(fmtInput);
    card.appendChild(fmtWrap);

    const decWrap = document.createElement("div");
    decWrap.className = "mb-3";
    decWrap.appendChild(_label(t("import.field.decimal")));
    const decSel = _select([[",", t("import.decimal.comma")], [".", t("import.decimal.dot")]], _parsed.detected_decimal_separator);
    decSel.id = "map-decimal";
    decWrap.appendChild(decSel);
    card.appendChild(decWrap);

    const catWrap = document.createElement("div");
    catWrap.className = "mb-6";
    catWrap.appendChild(_label(t("import.field.category")));
    const catSel = _select([["", "—"], ..._categories.map(c => [String(c.id), c.name])], "");
    catSel.id = "map-category";
    catWrap.appendChild(catSel);
    card.appendChild(catWrap);

    const btn = document.createElement("button");
    btn.className = "w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors";
    btn.textContent = t("import.btn.import");
    btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "…";
        await _doConfirm(card);
    });
    card.appendChild(btn);
}

async function _doConfirm(card) {
    const isOFX = _parsed.format !== "csv";
    const fieldMap = isOFX
        ? _parsed.suggested_mapping
        : {
            date: document.getElementById("map-date")?.value,
            amount: document.getElementById("map-amount")?.value,
            description: document.getElementById("map-description")?.value,
        };
    const dateFormat = isOFX
        ? _parsed.detected_date_format
        : (document.getElementById("map-date-format")?.value || "%d.%m.%Y");
    const decimalSep = isOFX
        ? _parsed.detected_decimal_separator
        : (document.getElementById("map-decimal")?.value || ",");
    const categoryRaw = document.getElementById("map-category")?.value || "";
    const categoryId = categoryRaw ? parseInt(categoryRaw) : null;
    const accountId = parseInt(_accountId || document.getElementById("import-account")?.value || "0");

    const r = await api.post("/import/confirm", {
        session_token: _parsed.session_token,
        account_id: accountId,
        category_id: categoryId,
        field_map: fieldMap,
        date_format: dateFormat,
        decimal_separator: decimalSep,
    });

    const main = document.querySelector("main");

    if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        if (err.detail === "session_expired") {
            toast(t("import.warn.sessionExpired"), "error");
            _step = 1;
        } else {
            toast(t("import.error.parseError"), "error");
        }
        _render(main);
        return;
    }

    const result = await r.json();
    _step = 3;
    _render(main);
    _renderStep3(document.querySelector(".glass"), result);
}

function _renderStep3(card, result) {
    if (!result) return;
    card.textContent = "";

    const countWrap = document.createElement("div");
    countWrap.className = "text-center mb-6";
    const count = document.createElement("div");
    count.className = "text-5xl font-bold text-emerald-400 mb-2";
    count.textContent = String(result.imported);
    const countLabel = document.createElement("div");
    countLabel.className = "text-gray-400 text-sm";
    countLabel.textContent = t("import.result.imported");
    countWrap.appendChild(count);
    countWrap.appendChild(countLabel);
    card.appendChild(countWrap);

    if (result.duplicates.length > 0) {
        toast(t("import.warn.duplicates"), "warning");
        card.appendChild(_collapsible(
            `${result.duplicates.length} ${t("import.result.duplicates")}`,
            result.duplicates.map(d => `${d.date} · ${d.amount} · ${d.description}`),
            "yellow",
        ));
    }

    if (result.errors.length > 0) {
        card.appendChild(_collapsible(
            `${result.errors.length} ${t("import.result.errors")}`,
            result.errors.map(e => `Zeile ${e.row}: ${e.reason}`),
            "red",
        ));
    }

    const btnRow = document.createElement("div");
    btnRow.className = "flex gap-3 mt-6";

    const toTx = document.createElement("button");
    toTx.className = "flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors";
    toTx.textContent = t("import.btn.toTransactions");
    toTx.addEventListener("click", () => navigate("#/transactions"));

    const restart = document.createElement("button");
    restart.className = "flex-1 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl text-sm font-medium transition-colors";
    restart.textContent = t("import.btn.restart");
    restart.addEventListener("click", () => renderImport());

    btnRow.appendChild(toTx);
    btnRow.appendChild(restart);
    card.appendChild(btnRow);
}

function _collapsible(header, items, color) {
    const wrap = document.createElement("div");
    const borderColor = color === "red" ? "border-red-800" : "border-yellow-800";
    const textColor = color === "red" ? "text-red-400" : "text-yellow-400";
    wrap.className = `border ${borderColor} rounded-xl mb-4 overflow-hidden`;

    const btn = document.createElement("button");
    btn.className = `w-full text-left px-4 py-3 text-sm font-medium ${textColor}`;
    btn.textContent = `▶ ${header}`;

    const list = document.createElement("div");
    list.className = "hidden px-4 pb-3";
    items.forEach(item => {
        const row = document.createElement("div");
        row.className = "text-xs text-gray-400 py-1 border-t border-gray-800";
        row.textContent = item;
        list.appendChild(row);
    });

    btn.addEventListener("click", () => {
        const open = !list.classList.contains("hidden");
        list.classList.toggle("hidden", open);
        btn.textContent = `${open ? "▶" : "▼"} ${header}`;
    });

    wrap.appendChild(btn);
    wrap.appendChild(list);
    return wrap;
}
