import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast } from "../toast.js";
import { countUp, animateProgressBars, fadeInUp, crossfade } from "../animations.js";

let _year = new Date().getFullYear();
let _month = new Date().getMonth() + 1;

function _monthLabel(year, month) {
    return new Date(year, month - 1, 1).toLocaleDateString(
        document.documentElement.lang === "de" ? "de-DE" : "en-US",
        { month: "long", year: "numeric" }
    );
}

function _buildSollIstRow(node, depth) {
    const row = document.createElement("div");
    row.style.cssText = `padding:0.75rem 1rem 0.75rem ${depth * 16 + 16}px;border-bottom:1px solid rgba(255,255,255,0.04);`;

    const pct = parseFloat(node.soll) > 0
        ? Math.min(100, Math.abs(parseFloat(node.ist) / parseFloat(node.soll) * 100))
        : 0;
    const over = pct >= 100;

    const top = document.createElement("div");
    top.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;";

    const nameEl = document.createElement("span");
    nameEl.style.cssText = "font-size:0.875rem;color:#cbd5e1;";
    nameEl.textContent = node.name;

    const vals = document.createElement("div");
    vals.style.cssText = "display:flex;gap:1.5rem;font-size:0.8rem;font-variant-numeric:tabular-nums;";

    const istEl = document.createElement("span");
    istEl.style.color = over ? "#f43f5e" : "#e2e8f0";
    istEl.textContent = `${parseFloat(node.ist).toFixed(2).replace(".", ",")} €`;

    const sollEl = document.createElement("span");
    sollEl.style.color = "#64748b";
    sollEl.textContent = `/ ${parseFloat(node.soll).toFixed(2).replace(".", ",")} €`;

    vals.appendChild(istEl);
    vals.appendChild(sollEl);
    top.appendChild(nameEl);
    top.appendChild(vals);

    const barBg = document.createElement("div");
    barBg.style.cssText = "height:3px;border-radius:2px;background:rgba(255,255,255,0.06);overflow:hidden;";
    const bar = document.createElement("div");
    bar.style.cssText = "height:100%;border-radius:2px;";
    bar.dataset.pct = String(pct);
    bar.style.background = over
        ? "linear-gradient(90deg,#f97316,#f43f5e)"
        : "linear-gradient(90deg,#6366f1,#10b981)";
    barBg.appendChild(bar);
    row.appendChild(top);
    row.appendChild(barBg);

    if (node.children && node.children.length > 0) {
        node.children.forEach(child => row.appendChild(_buildSollIstRow(child, depth + 1)));
    }
    return row;
}

async function _loadDashboard(mainEl) {
    const [summaryRes, sollIstRes, balancesRes] = await Promise.all([
        api.get(`/transactions/summary?year=${_year}&month=${_month}`),
        api.get(`/categories/soll-ist?year=${_year}&month=${_month}`),
        api.get("/accounts/balances"),
    ]);
    if (!summaryRes.ok || !sollIstRes.ok || !balancesRes.ok) {
        toast(t("errors.generic"), "error");
        return;
    }
    const summary = await summaryRes.json();
    const sollIst = await sollIstRes.json();
    const balances = await balancesRes.json();

    const monthLabel = mainEl.querySelector("#dash-month-label");
    if (monthLabel) monthLabel.textContent = _monthLabel(_year, _month);

    const incEl = mainEl.querySelector("#dash-income");
    const expEl = mainEl.querySelector("#dash-expenses");
    const balEl = mainEl.querySelector("#dash-balance");
    if (incEl) countUp(incEl, summary.income);
    if (expEl) countUp(expEl, summary.expenses);
    if (balEl) countUp(balEl, summary.balance);

    const sollIstBox = mainEl.querySelector("#dash-soll-ist");
    if (sollIstBox) {
        sollIstBox.textContent = "";
        if (sollIst.length === 0) {
            const empty = document.createElement("p");
            empty.style.cssText = "color:#475569;font-size:0.875rem;padding:1.5rem;text-align:center;";
            empty.textContent = t("dashboard.noData");
            sollIstBox.appendChild(empty);
        } else {
            sollIst.forEach(node => sollIstBox.appendChild(_buildSollIstRow(node, 0)));
            animateProgressBars(sollIstBox);
        }
    }

    const balBox = mainEl.querySelector("#dash-balances");
    if (balBox) {
        balBox.textContent = "";
        balances.forEach(acc => {
            const card = document.createElement("div");
            card.className = "glass";
            card.style.cssText = "border-radius:0.75rem;padding:0.875rem 1rem;display:flex;justify-content:space-between;align-items:center;";
            const nameEl = document.createElement("span");
            nameEl.style.cssText = "font-size:0.875rem;color:#94a3b8;";
            nameEl.textContent = acc.name;
            const valEl = document.createElement("span");
            const bal = parseFloat(acc.balance);
            valEl.style.cssText = `font-size:0.9rem;font-weight:600;color:${bal >= 0 ? "#10b981" : "#f43f5e"};`;
            valEl.textContent = `${bal >= 0 ? "+" : ""}${bal.toFixed(2).replace(".", ",")} €`;
            card.appendChild(nameEl);
            card.appendChild(valEl);
            balBox.appendChild(card);
        });
        fadeInUp(Array.from(balBox.children), 40);
    }
}

export async function renderDashboard() {
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

    // ── Header row (month nav + add button)
    const headerRow = document.createElement("div");
    headerRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:2rem;flex-wrap:wrap;gap:1rem;";

    const monthNav = document.createElement("div");
    monthNav.style.cssText = "display:flex;align-items:center;gap:1rem;";

    const btnStyle = "padding:0.4rem 0.875rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.12);background:rgba(255,255,255,0.04);color:#94a3b8;cursor:pointer;font-size:1rem;transition:all 0.15s;";
    const prevBtn = document.createElement("button");
    prevBtn.style.cssText = btnStyle;
    prevBtn.textContent = "←";

    const monthLabel = document.createElement("span");
    monthLabel.id = "dash-month-label";
    monthLabel.style.cssText = "font-size:1.125rem;font-weight:600;color:#e2e8f0;min-width:12rem;text-align:center;";
    monthLabel.textContent = _monthLabel(_year, _month);

    const nextBtn = document.createElement("button");
    nextBtn.style.cssText = btnStyle;
    nextBtn.textContent = "→";

    monthNav.appendChild(prevBtn);
    monthNav.appendChild(monthLabel);
    monthNav.appendChild(nextBtn);

    const addTxBtn = document.createElement("button");
    addTxBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;box-shadow:0 4px 20px rgba(99,102,241,0.3);transition:opacity 0.15s;";
    addTxBtn.textContent = t("dashboard.addTransaction");
    addTxBtn.addEventListener("mouseover", () => { addTxBtn.style.opacity = "0.85"; });
    addTxBtn.addEventListener("mouseout", () => { addTxBtn.style.opacity = "1"; });
    addTxBtn.addEventListener("click", () => navigate("#/transactions"));

    headerRow.appendChild(monthNav);
    headerRow.appendChild(addTxBtn);
    main.appendChild(headerRow);

    // ── Summary cards
    const summaryGrid = document.createElement("div");
    summaryGrid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem;";

    const cardDefs = [
        { id: "dash-income",   label: t("dashboard.income"),   color: "#10b981" },
        { id: "dash-expenses", label: t("dashboard.expenses"), color: "#f43f5e" },
        { id: "dash-balance",  label: t("dashboard.balance"),  color: "#818cf8" },
    ];
    cardDefs.forEach(({ id, label, color }) => {
        const card = document.createElement("div");
        card.className = "glass glow-accent";
        card.style.cssText = "border-radius:1rem;padding:1.25rem 1.5rem;";
        const lbl = document.createElement("p");
        lbl.style.cssText = "font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;margin-bottom:0.5rem;";
        lbl.textContent = label;
        const val = document.createElement("p");
        val.id = id;
        val.style.cssText = `font-size:1.75rem;font-weight:700;color:${color};font-variant-numeric:tabular-nums;`;
        val.textContent = "—";
        card.appendChild(lbl);
        card.appendChild(val);
        summaryGrid.appendChild(card);
    });
    main.appendChild(summaryGrid);
    fadeInUp(Array.from(summaryGrid.children), 60);

    // ── Soll/Ist
    const sollIstSection = document.createElement("div");
    sollIstSection.className = "glass";
    sollIstSection.style.cssText = "border-radius:1rem;margin-bottom:2rem;overflow:hidden;";

    const sollIstHeader = document.createElement("div");
    sollIstHeader.style.cssText = "padding:1rem 1.25rem;border-bottom:1px solid rgba(255,255,255,0.06);";
    const sollIstTitle = document.createElement("h2");
    sollIstTitle.style.cssText = "font-size:0.8rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;";
    sollIstTitle.textContent = t("dashboard.sollIst");
    sollIstHeader.appendChild(sollIstTitle);

    const sollIstBox = document.createElement("div");
    sollIstBox.id = "dash-soll-ist";

    sollIstSection.appendChild(sollIstHeader);
    sollIstSection.appendChild(sollIstBox);
    main.appendChild(sollIstSection);

    // ── Account balances
    const balHeader = document.createElement("h2");
    balHeader.style.cssText = "font-size:0.8rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.75rem;";
    balHeader.textContent = t("dashboard.accounts");

    const balBox = document.createElement("div");
    balBox.id = "dash-balances";
    balBox.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;";

    main.appendChild(balHeader);
    main.appendChild(balBox);
    wrapper.appendChild(main);

    app.textContent = "";
    app.appendChild(wrapper);

    await renderNav(navContainer);

    prevBtn.addEventListener("click", () => {
        _month--;
        if (_month < 1) { _month = 12; _year--; }
        crossfade(main, () => _loadDashboard(main));
    });
    nextBtn.addEventListener("click", () => {
        _month++;
        if (_month > 12) { _month = 1; _year++; }
        crossfade(main, () => _loadDashboard(main));
    });

    await _loadDashboard(main);
}
