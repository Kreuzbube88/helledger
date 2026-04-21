import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast, confirmDialog } from "../toast.js";
import { fadeInUp } from "../animations.js";

let _year = new Date().getFullYear();
let _month = new Date().getMonth() + 1;
let _filterAccount = "";
let _filterCategory = "";
let _accounts = [];
let _categories = [];

function _flatCats(list) {
    const result = [];
    function walk(items) {
        items.forEach(c => { result.push(c); if (c.children) walk(c.children); });
    }
    walk(list);
    return result;
}

function _monthKey() {
    return `${_year}-${String(_month).padStart(2, "0")}`;
}

function _fmtAmount(str, type) {
    const n = parseFloat(str);
    const color = type === "transfer" ? "#8b5cf6" : n >= 0 ? "#10b981" : "#f43f5e";
    const sign = n >= 0 ? "+" : "";
    return { text: `${sign}${n.toFixed(2).replace(".", ",")} €`, color };
}

function _inp(form, id, label, type, value) {
    const wrap = document.createElement("div");
    const lbl = document.createElement("label");
    lbl.style.cssText = "font-size:0.8rem;color:#64748b;display:block;margin-bottom:0.3rem;";
    lbl.textContent = label;
    lbl.htmlFor = id;
    const inp = document.createElement("input");
    inp.id = id; inp.name = id; inp.type = type;
    if (value !== undefined) inp.value = value;
    inp.style.cssText = "width:100%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.6rem 0.875rem;color:#e2e8f0;font-size:0.9rem;outline:none;";
    inp.addEventListener("focus", () => { inp.style.borderColor = "rgba(99,102,241,0.6)"; });
    inp.addEventListener("blur", () => { inp.style.borderColor = "rgba(255,255,255,0.1)"; });
    wrap.appendChild(lbl);
    wrap.appendChild(inp);
    form.appendChild(wrap);
    return inp;
}

function _sel(form, id, label, options, value) {
    const wrap = document.createElement("div");
    const lbl = document.createElement("label");
    lbl.style.cssText = "font-size:0.8rem;color:#64748b;display:block;margin-bottom:0.3rem;";
    lbl.textContent = label;
    lbl.htmlFor = id;
    const sel = document.createElement("select");
    sel.id = id; sel.name = id;
    sel.style.cssText = "width:100%;background:rgba(10,10,20,0.9);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.6rem 0.875rem;color:#e2e8f0;font-size:0.9rem;outline:none;";
    sel.addEventListener("focus", () => { sel.style.borderColor = "rgba(99,102,241,0.6)"; });
    sel.addEventListener("blur", () => { sel.style.borderColor = "rgba(255,255,255,0.1)"; });
    options.forEach(({ val, lbl: optLbl }) => {
        const opt = document.createElement("option");
        opt.value = val; opt.textContent = optLbl;
        if (val === String(value ?? "")) opt.selected = true;
        sel.appendChild(opt);
    });
    wrap.appendChild(lbl);
    wrap.appendChild(sel);
    form.appendChild(wrap);
    return sel;
}

function _modal(title, bodyFn, onSubmit) {
    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
        position: "fixed", inset: "0",
        background: "rgba(0,0,0,0.7)",
        backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: "10000", opacity: "0", transition: "opacity 0.2s ease",
    });
    const box = document.createElement("div");
    Object.assign(box.style, {
        background: "rgba(10,10,20,0.97)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "1.25rem",
        padding: "2rem",
        width: "min(480px,90vw)",
        maxHeight: "85vh",
        overflowY: "auto",
        transform: "scale(0.88) translateY(20px)",
        transition: "transform 0.35s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s ease",
        opacity: "0",
    });
    const h2 = document.createElement("h2");
    h2.style.cssText = "font-size:1.125rem;font-weight:600;color:#e2e8f0;margin-bottom:1.5rem;";
    h2.textContent = title;
    box.appendChild(h2);

    const form = document.createElement("form");
    form.style.cssText = "display:flex;flex-direction:column;gap:1rem;";
    bodyFn(form);

    const row = document.createElement("div");
    row.style.cssText = "display:flex;gap:0.75rem;justify-content:flex-end;margin-top:0.5rem;";

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.15);background:transparent;color:#94a3b8;cursor:pointer;font-size:0.875rem;";
    cancelBtn.textContent = t("transactions.cancel");

    const submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.5rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;";
    submitBtn.textContent = t("transactions.save");

    row.appendChild(cancelBtn);
    row.appendChild(submitBtn);
    form.appendChild(row);
    box.appendChild(form);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
        overlay.style.opacity = "1";
        box.style.transform = "scale(1) translateY(0)";
        box.style.opacity = "1";
    });

    const close = () => {
        overlay.style.opacity = "0";
        box.style.transform = "scale(0.95) translateY(10px)";
        box.style.opacity = "0";
        setTimeout(() => overlay.remove(), 250);
    };
    cancelBtn.addEventListener("click", close);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.6";
        try { await onSubmit(form, close); }
        finally { submitBtn.disabled = false; submitBtn.style.opacity = "1"; }
    });
}

function _openAdd(onDone) {
    _modal(t("transactions.add"), (form) => {
        const typeOpts = [
            { val: "expense", lbl: t("transactions.expense") },
            { val: "income", lbl: t("transactions.income") },
        ];
        _sel(form, "transaction_type", t("transactions.type"), typeOpts, "expense");
        _sel(form, "account_id", t("transactions.account"), _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name })));
        _sel(form, "category_id", t("transactions.category"), _categories.map(c => ({ val: String(c.id), lbl: c.name })));
        _inp(form, "amount", t("transactions.amount"), "number", "0.00");
        _inp(form, "date", t("transactions.date"), "date", new Date().toISOString().slice(0, 10));
        _inp(form, "description", t("transactions.description"), "text");
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.post("/transactions", {
            account_id: parseInt(d.account_id),
            category_id: parseInt(d.category_id),
            amount: d.amount,
            date: d.date,
            description: d.description,
            transaction_type: d.transaction_type,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.add"), "success");
        close();
        onDone();
    });
}

function _openTransfer(onDone) {
    _modal(t("transactions.addTransfer"), (form) => {
        const accOpts = _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name }));
        _sel(form, "from_account_id", t("transactions.fromAccount"), accOpts);
        _sel(form, "to_account_id", t("transactions.toAccount"), accOpts);
        _inp(form, "amount", t("transactions.amount"), "number", "0.00");
        _inp(form, "date", t("transactions.date"), "date", new Date().toISOString().slice(0, 10));
        _inp(form, "description", t("transactions.description"), "text");
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.post("/transactions/transfer", {
            from_account_id: parseInt(d.from_account_id),
            to_account_id: parseInt(d.to_account_id),
            amount: d.amount,
            date: d.date,
            description: d.description,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.addTransfer"), "success");
        close();
        onDone();
    });
}

function _openEdit(tx, onDone) {
    _modal(t("transactions.edit"), (form) => {
        const typeOpts = [
            { val: "expense", lbl: t("transactions.expense") },
            { val: "income", lbl: t("transactions.income") },
        ];
        _sel(form, "transaction_type", t("transactions.type"), typeOpts, tx.transaction_type);
        _sel(form, "account_id", t("transactions.account"),
            _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name })),
            String(tx.account_id));
        _sel(form, "category_id", t("transactions.category"),
            _categories.map(c => ({ val: String(c.id), lbl: c.name })),
            tx.category_id ? String(tx.category_id) : "");
        _inp(form, "amount", t("transactions.amount"), "number", Math.abs(parseFloat(tx.amount)).toFixed(2));
        _inp(form, "date", t("transactions.date"), "date", tx.date);
        _inp(form, "description", t("transactions.description"), "text", tx.description);
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.patch(`/transactions/${tx.id}`, {
            account_id: parseInt(d.account_id),
            category_id: d.category_id ? parseInt(d.category_id) : null,
            amount: d.amount,
            date: d.date,
            description: d.description,
            transaction_type: d.transaction_type,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.save"), "success");
        close();
        onDone();
    });
}

async function _loadTable(tbody) {
    let url = `/transactions?year=${_year}&month=${_month}`;
    if (_filterAccount) url += `&account_id=${_filterAccount}`;
    if (_filterCategory) url += `&category_id=${_filterCategory}`;
    const res = await api.get(url);
    if (!res.ok) { toast(t("errors.generic"), "error"); return; }
    const txs = await res.json();
    tbody.textContent = "";

    if (txs.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 6;
        td.style.cssText = "text-align:center;padding:2.5rem;color:#475569;font-size:0.875rem;";
        td.textContent = t("transactions.noData");
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    txs.forEach(tx => {
        const accName = _accounts.find(a => a.id === tx.account_id)?.name ?? "—";
        const catObj = _categories.find(c => c.id === tx.category_id);
        const catName = catObj ? catObj.name
            : (tx.transaction_type === "transfer" ? t("transactions.transfer") : "—");
        const { text: amtText, color: amtColor } = _fmtAmount(tx.amount, tx.transaction_type);

        const tr = document.createElement("tr");
        tr.style.cssText = "border-bottom:1px solid rgba(255,255,255,0.04);transition:background 0.1s;";
        tr.addEventListener("mouseover", () => { tr.style.background = "rgba(255,255,255,0.02)"; });
        tr.addEventListener("mouseout", () => { tr.style.background = "transparent"; });

        const cellDefs = [
            { text: tx.date, s: "color:#64748b;font-size:0.8rem;" },
            { text: tx.description, s: "color:#e2e8f0;" },
            { text: catName, s: "color:#94a3b8;font-size:0.85rem;" },
            { text: accName, s: "color:#94a3b8;font-size:0.85rem;" },
            { text: amtText, s: `color:${amtColor};font-weight:600;font-variant-numeric:tabular-nums;text-align:right;` },
        ];
        cellDefs.forEach(({ text, s }) => {
            const td = document.createElement("td");
            td.style.cssText = `padding:0.75rem 1rem;${s}`;
            td.textContent = text;
            tr.appendChild(td);
        });

        const actionTd = document.createElement("td");
        actionTd.style.cssText = "padding:0.5rem 1rem;text-align:right;white-space:nowrap;";

        if (tx.transaction_type !== "transfer") {
            const editBtn = document.createElement("button");
            editBtn.style.cssText = "font-size:0.75rem;color:#6366f1;background:none;border:none;cursor:pointer;margin-right:0.5rem;";
            editBtn.textContent = t("transactions.edit");
            editBtn.addEventListener("click", () => _openEdit(tx, () => _loadTable(tbody)));
            actionTd.appendChild(editBtn);
        }

        const delBtn = document.createElement("button");
        delBtn.style.cssText = "font-size:0.75rem;color:#f43f5e;background:none;border:none;cursor:pointer;";
        delBtn.textContent = t("transactions.delete");
        delBtn.addEventListener("click", () => {
            confirmDialog(t("transactions.confirmDelete"), async () => {
                const r = await api.delete(`/transactions/${tx.id}`);
                if (!r.ok) { toast(t("errors.generic"), "error"); return; }
                toast(t("transactions.delete"), "success");
                _loadTable(tbody);
            });
        });
        actionTd.appendChild(delBtn);
        tr.appendChild(actionTd);
        tbody.appendChild(tr);
    });
    fadeInUp(Array.from(tbody.querySelectorAll("tr")), 20);
}

export async function renderTransactions() {
    const user = await getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    const app = document.getElementById("app");
    const wrapper = document.createElement("div");
    wrapper.style.cssText = "min-height:100dvh;color:white;";

    const navContainer = document.createElement("div");
    navContainer.id = "nav-container";
    wrapper.appendChild(navContainer);

    const main = document.createElement("main");
    main.style.cssText = "padding:2rem;max-width:72rem;margin:0 auto;";

    // Load reference data
    const [accRes, catRes] = await Promise.all([api.get("/accounts"), api.get("/categories")]);
    _accounts = accRes.ok ? await accRes.json() : [];
    const catTree = catRes.ok ? await catRes.json() : [];
    _categories = _flatCats(catTree);

    // Header
    const headerRow = document.createElement("div");
    headerRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;";

    const title = document.createElement("h1");
    title.style.cssText = "font-size:1.5rem;font-weight:700;color:#e2e8f0;";
    title.textContent = t("transactions.title");

    const btnGroup = document.createElement("div");
    btnGroup.style.cssText = "display:flex;gap:0.75rem;";

    const addBtn = document.createElement("button");
    addBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;box-shadow:0 4px 20px rgba(99,102,241,0.3);";
    addBtn.textContent = t("transactions.add");

    const transferBtn = document.createElement("button");
    transferBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:1px solid rgba(139,92,246,0.4);background:rgba(139,92,246,0.1);color:#a78bfa;cursor:pointer;font-size:0.875rem;";
    transferBtn.textContent = t("transactions.addTransfer");

    btnGroup.appendChild(addBtn);
    btnGroup.appendChild(transferBtn);
    headerRow.appendChild(title);
    headerRow.appendChild(btnGroup);
    main.appendChild(headerRow);

    // Filters
    const filterRow = document.createElement("div");
    filterRow.style.cssText = "display:flex;gap:0.75rem;margin-bottom:1.5rem;flex-wrap:wrap;";

    const inputStyle = "background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.4rem 0.75rem;color:#e2e8f0;font-size:0.85rem;outline:none;";

    const monthInp = document.createElement("input");
    monthInp.type = "month";
    monthInp.value = _monthKey();
    monthInp.style.cssText = inputStyle;

    const accFilter = document.createElement("select");
    accFilter.style.cssText = inputStyle;
    const allAccOpt = document.createElement("option");
    allAccOpt.value = ""; allAccOpt.textContent = t("transactions.filterAccount");
    accFilter.appendChild(allAccOpt);
    _accounts.forEach(a => {
        const o = document.createElement("option"); o.value = String(a.id); o.textContent = a.name;
        accFilter.appendChild(o);
    });

    const catFilter = document.createElement("select");
    catFilter.style.cssText = inputStyle;
    const allCatOpt = document.createElement("option");
    allCatOpt.value = ""; allCatOpt.textContent = t("transactions.filterCategory");
    catFilter.appendChild(allCatOpt);
    _categories.forEach(c => {
        const o = document.createElement("option"); o.value = String(c.id); o.textContent = c.name;
        catFilter.appendChild(o);
    });

    filterRow.appendChild(monthInp);
    filterRow.appendChild(accFilter);
    filterRow.appendChild(catFilter);
    main.appendChild(filterRow);

    // Table
    const tableWrap = document.createElement("div");
    tableWrap.className = "glass";
    tableWrap.style.cssText = "border-radius:1rem;overflow:hidden;";

    const table = document.createElement("table");
    table.style.cssText = "width:100%;border-collapse:collapse;";

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.style.cssText = "border-bottom:1px solid rgba(255,255,255,0.06);";
    const thDefs = [
        t("transactions.date"), t("transactions.description"),
        t("transactions.category"), t("transactions.account"),
        t("transactions.amount"), "",
    ];
    thDefs.forEach((lbl, i) => {
        const th = document.createElement("th");
        th.style.cssText = "padding:0.75rem 1rem;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#475569;";
        if (i === 4) th.style.textAlign = "right";
        th.textContent = lbl;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    main.appendChild(tableWrap);

    wrapper.appendChild(main);
    app.textContent = "";
    app.appendChild(wrapper);

    await renderNav(navContainer);

    monthInp.addEventListener("change", () => {
        const parts = monthInp.value.split("-").map(Number);
        _year = parts[0]; _month = parts[1];
        _loadTable(tbody);
    });
    accFilter.addEventListener("change", () => { _filterAccount = accFilter.value; _loadTable(tbody); });
    catFilter.addEventListener("change", () => { _filterCategory = catFilter.value; _loadTable(tbody); });
    addBtn.addEventListener("click", () => _openAdd(() => _loadTable(tbody)));
    transferBtn.addEventListener("click", () => _openTransfer(() => _loadTable(tbody)));

    await _loadTable(tbody);
}
