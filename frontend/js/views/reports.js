// frontend/js/views/reports.js
import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast } from "../toast.js";
import { fadeInUp } from "../animations.js";

const DONUT_COLORS = [
    "#6366f1", "#10b981", "#f59e0b", "#3b82f6",
    "#ec4899", "#8b5cf6", "#14b8a6", "#f97316",
];

let _state = {
    mode: "month",
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    fromDate: null,
    toDate: null,
    accountId: null,
    accounts: [],
    charts: {},
    lastData: {},
};

function _isoDate(y, m, d) {
    return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function _lastDayOfMonth(y, m) {
    return new Date(y, m, 0).getDate();
}

function _buildDateRange() {
    if (_state.mode === "month") {
        return {
            from_date: _isoDate(_state.year, _state.month, 1),
            to_date: _isoDate(_state.year, _state.month, _lastDayOfMonth(_state.year, _state.month)),
        };
    }
    if (_state.mode === "year") {
        return { from_date: `${_state.year}-01-01`, to_date: `${_state.year}-12-31` };
    }
    return { from_date: _state.fromDate, to_date: _state.toDate };
}

function _buildQs() {
    const { from_date, to_date } = _buildDateRange();
    const p = new URLSearchParams({ from_date, to_date });
    if (_state.accountId) p.set("account_id", String(_state.accountId));
    return p.toString();
}

function _destroyCharts() {
    for (const c of Object.values(_state.charts)) { if (c) c.destroy(); }
    _state.charts = {};
}

function _setChartDefaults() {
    if (!window.Chart) return;
    Chart.defaults.color = "#94a3b8";
    Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
    Chart.defaults.font.family = "inherit";
}

function _showNoData(canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#475569";
    ctx.font = "14px inherit";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(t("reports.noData"), canvas.width / 2, canvas.height / 2);
}

function _renderDonut(canvas, data) {
    if (_state.charts.donut) { _state.charts.donut.destroy(); delete _state.charts.donut; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["expenses-by-category"] = data;
    _state.charts.donut = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: data.map((d) => d.category_name),
            datasets: [{
                data: data.map((d) => parseFloat(d.total)),
                backgroundColor: data.map((_, i) => DONUT_COLORS[i % DONUT_COLORS.length]),
                borderWidth: 0,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: "right", labels: { boxWidth: 12, padding: 16 } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} \u20ac`,
                    },
                },
            },
        },
    });
}

function _renderMonthlyTrend(canvas, data) {
    if (_state.charts.trend) { _state.charts.trend.destroy(); delete _state.charts.trend; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["monthly-trend"] = data;
    const lang = document.documentElement.lang === "de" ? "de-DE" : "en-US";
    const labels = data.map((d) =>
        new Date(d.year, d.month - 1, 1).toLocaleDateString(lang, { month: "short", year: "2-digit" })
    );
    _state.charts.trend = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: t("dashboard.income"),
                    data: data.map((d) => parseFloat(d.income)),
                    backgroundColor: "rgba(16,185,129,0.7)",
                    borderColor: "#10b981",
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: t("dashboard.expenses"),
                    data: data.map((d) => parseFloat(d.expenses)),
                    backgroundColor: "rgba(244,63,94,0.7)",
                    borderColor: "#f43f5e",
                    borderWidth: 1,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, beginAtZero: true },
            },
        },
    });
}

function _renderBalanceHistory(canvas, data) {
    if (_state.charts.balance) { _state.charts.balance.destroy(); delete _state.charts.balance; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["balance-history"] = data;
    _state.charts.balance = new Chart(canvas, {
        type: "line",
        data: {
            labels: data.map((d) => d.date),
            datasets: [{
                label: t("reports.chart.balanceHistory"),
                data: data.map((d) => parseFloat(d.balance)),
                borderColor: "#6366f1",
                backgroundColor: "rgba(99,102,241,0.12)",
                fill: true,
                tension: 0.3,
                pointRadius: data.length > 60 ? 0 : 3,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { maxTicksLimit: 8 },
                },
                y: { grid: { color: "rgba(255,255,255,0.04)" } },
            },
        },
    });
}

function _renderSollIst(canvas, data) {
    if (_state.charts.sollIst) { _state.charts.sollIst.destroy(); delete _state.charts.sollIst; }
    const flat = (data || []).filter(
        (n) => parseFloat(n.soll) !== 0 || parseFloat(n.ist) !== 0
    );
    if (flat.length === 0) { _showNoData(canvas); return; }
    _state.lastData["soll-ist"] = data;
    _state.charts.sollIst = new Chart(canvas, {
        type: "bar",
        data: {
            labels: flat.map((n) => n.name),
            datasets: [
                {
                    label: t("dashboard.soll"),
                    data: flat.map((n) => parseFloat(n.soll)),
                    backgroundColor: "rgba(99,102,241,0.6)",
                    borderColor: "#6366f1",
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: t("dashboard.ist"),
                    data: flat.map((n) => Math.abs(parseFloat(n.ist))),
                    backgroundColor: "rgba(16,185,129,0.6)",
                    borderColor: "#10b981",
                    borderWidth: 1,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, beginAtZero: true },
                y: { grid: { color: "rgba(255,255,255,0.04)" } },
            },
        },
    });
}

async function _loadAllCharts() {
    const { from_date, to_date } = _buildDateRange();
    if (!from_date || !to_date || from_date > to_date) return;

    const qs = _buildQs();
    const [catRes, trendRes, sollIstRes] = await Promise.all([
        api.get(`/reports/expenses-by-category?${qs}`),
        api.get(`/reports/monthly-trend?${qs}`),
        api.get(`/reports/soll-ist?${qs}`),
    ]);

    if (catRes.ok) _renderDonut(document.getElementById("canvas-donut"), await catRes.json());
    else toast(t("errors.generic"), "error");

    if (trendRes.ok) _renderMonthlyTrend(document.getElementById("canvas-trend"), await trendRes.json());
    else toast(t("errors.generic"), "error");

    if (sollIstRes.ok) _renderSollIst(document.getElementById("canvas-sollist"), await sollIstRes.json());
    else toast(t("errors.generic"), "error");

    const balCanvas = document.getElementById("canvas-balance");
    const balPlaceholder = document.getElementById("balance-placeholder");

    if (_state.accountId) {
        balCanvas.style.display = "";
        if (balPlaceholder) balPlaceholder.style.display = "none";
        const balRes = await api.get(
            `/reports/balance-history?from_date=${from_date}&to_date=${to_date}&account_id=${_state.accountId}`
        );
        if (balRes.ok) _renderBalanceHistory(balCanvas, await balRes.json());
        else toast(t("errors.generic"), "error");
    } else {
        if (_state.charts.balance) { _state.charts.balance.destroy(); delete _state.charts.balance; }
        balCanvas.style.display = "none";
        if (balPlaceholder) balPlaceholder.style.display = "";
    }
}

function _downloadPng(chartKey, filename) {
    const chart = _state.charts[chartKey];
    if (!chart) return;
    const a = document.createElement("a");
    a.href = chart.canvas.toDataURL("image/png");
    a.download = filename;
    a.click();
}

function _downloadCsv(dataKey, filename) {
    const raw = _state.lastData[dataKey];
    if (!raw) return;
    let rows = raw;
    if (dataKey === "soll-ist") {
        function flatten(nodes) {
            return nodes.flatMap((n) => [
                { id: n.id, name: n.name, category_type: n.category_type, soll: n.soll, ist: n.ist, diff: n.diff },
                ...flatten(n.children || []),
            ]);
        }
        rows = flatten(raw);
    }
    if (!rows.length) return;
    const headers = Object.keys(rows[0]).join(",");
    const body = rows.map((r) => Object.values(r).map((v) => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([headers + "\n" + body], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
}

function _exportBtn(label, onClick) {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.className = "text-xs text-gray-400 hover:text-indigo-400 transition-colors";
    btn.addEventListener("click", onClick);
    return btn;
}

function _chartCard(canvasId, titleKey, placeholderId) {
    const chartKeyMap = {
        "canvas-donut": "donut",
        "canvas-trend": "trend",
        "canvas-balance": "balance",
        "canvas-sollist": "sollIst",
    };
    const dataKeyMap = {
        "canvas-donut": "expenses-by-category",
        "canvas-trend": "monthly-trend",
        "canvas-balance": "balance-history",
        "canvas-sollist": "soll-ist",
    };
    const chartKey = chartKeyMap[canvasId];
    const dataKey = dataKeyMap[canvasId];

    const card = document.createElement("div");
    card.className = "glass rounded-2xl p-6 flex flex-col gap-3";

    const header = document.createElement("div");
    header.className = "flex items-center justify-between";

    const title = document.createElement("h3");
    title.className = "text-xs font-semibold text-gray-400 uppercase tracking-wider";
    title.textContent = t(titleKey);
    header.appendChild(title);

    const exportWrap = document.createElement("div");
    exportWrap.className = "flex gap-3";
    exportWrap.appendChild(_exportBtn(t("reports.export.png"), () => _downloadPng(chartKey, `${dataKey}.png`)));
    exportWrap.appendChild(_exportBtn(t("reports.export.csv"), () => _downloadCsv(dataKey, `${dataKey}.csv`)));
    header.appendChild(exportWrap);
    card.appendChild(header);

    if (placeholderId) {
        const placeholder = document.createElement("div");
        placeholder.id = placeholderId;
        placeholder.className = "flex items-center justify-center h-40 text-gray-500 text-sm";
        placeholder.textContent = t("reports.selectAccount");
        placeholder.style.display = _state.accountId ? "none" : "";
        card.appendChild(placeholder);
    }

    const canvas = document.createElement("canvas");
    canvas.id = canvasId;
    if (placeholderId) canvas.style.display = _state.accountId ? "" : "none";
    card.appendChild(canvas);

    return card;
}

function _renderPickers(wrap) {
    wrap.replaceChildren();
    const lang = document.documentElement.lang === "de" ? "de-DE" : "en-US";

    if (_state.mode === "month") {
        const mSel = document.createElement("select");
        mSel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        for (let m = 1; m <= 12; m++) {
            const opt = document.createElement("option");
            opt.value = String(m);
            opt.textContent = new Date(2000, m - 1, 1).toLocaleDateString(lang, { month: "long" });
            opt.selected = m === _state.month;
            mSel.appendChild(opt);
        }
        mSel.addEventListener("change", () => { _state.month = parseInt(mSel.value); _loadAllCharts(); });
        wrap.appendChild(mSel);
    }

    if (_state.mode === "month" || _state.mode === "year") {
        const ySel = document.createElement("select");
        ySel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        const curYear = new Date().getFullYear();
        for (let y = curYear - 2; y <= curYear + 1; y++) {
            const opt = document.createElement("option");
            opt.value = String(y);
            opt.textContent = String(y);
            opt.selected = y === _state.year;
            ySel.appendChild(opt);
        }
        ySel.addEventListener("change", () => { _state.year = parseInt(ySel.value); _loadAllCharts(); });
        wrap.appendChild(ySel);
    }

    if (_state.mode === "custom") {
        if (!_state.fromDate) _state.fromDate = _isoDate(_state.year, _state.month, 1);
        if (!_state.toDate) _state.toDate = _isoDate(_state.year, _state.month, _lastDayOfMonth(_state.year, _state.month));

        const fromIn = document.createElement("input");
        fromIn.type = "date";
        fromIn.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        fromIn.value = _state.fromDate;

        const sep = document.createElement("span");
        sep.className = "text-gray-500 text-sm";
        sep.textContent = "\u2192";

        const toIn = document.createElement("input");
        toIn.type = "date";
        toIn.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        toIn.value = _state.toDate;

        function onDateChange() {
            if (fromIn.value && toIn.value && fromIn.value <= toIn.value) {
                _state.fromDate = fromIn.value;
                _state.toDate = toIn.value;
                _loadAllCharts();
            }
        }
        fromIn.addEventListener("change", onDateChange);
        toIn.addEventListener("change", onDateChange);
        wrap.appendChild(fromIn);
        wrap.appendChild(sep);
        wrap.appendChild(toIn);
    }
}

export async function renderReports() {
    const user = getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    _destroyCharts();
    _state.lastData = {};
    _state.mode = "month";
    _state.year = new Date().getFullYear();
    _state.month = new Date().getMonth() + 1;
    _state.fromDate = null;
    _state.toDate = null;
    _state.accountId = null;
    _state.accounts = [];

    const app = document.getElementById("app");
    app.replaceChildren();

    const navContainer = document.createElement("div");
    app.appendChild(navContainer);
    await renderNav(navContainer);

    const accRes = await api.get("/accounts");
    if (!accRes.ok) { navigate("#/settings"); return; }
    _state.accounts = await accRes.json();

    const main = document.createElement("main");
    main.className = "relative z-10 max-w-screen-xl mx-auto px-4 py-8 space-y-6";

    const pageTitle = document.createElement("h1");
    pageTitle.className = "text-2xl font-bold text-white";
    pageTitle.textContent = t("reports.title");
    main.appendChild(pageTitle);

    // Filter bar
    const filterCard = document.createElement("div");
    filterCard.className = "glass rounded-2xl p-4 flex flex-wrap items-center gap-4";

    const modeWrap = document.createElement("div");
    modeWrap.className = "flex rounded-lg overflow-hidden border border-gray-700";
    const MODES = ["month", "year", "custom"];
    const MODE_KEYS = {
        month: "reports.period.month",
        year: "reports.period.year",
        custom: "reports.period.custom",
    };
    const modeBtns = [];
    MODES.forEach((mode) => {
        const btn = document.createElement("button");
        btn.className = `px-4 py-2 text-sm transition-colors ${_state.mode === mode ? "bg-indigo-600 text-white" : "bg-transparent text-gray-400 hover:text-white"}`;
        btn.textContent = t(MODE_KEYS[mode]);
        btn.addEventListener("click", () => {
            _state.mode = mode;
            modeBtns.forEach((b, i) => {
                b.className = `px-4 py-2 text-sm transition-colors ${MODES[i] === mode ? "bg-indigo-600 text-white" : "bg-transparent text-gray-400 hover:text-white"}`;
            });
            _renderPickers(pickerWrap);
            _loadAllCharts();
        });
        modeBtns.push(btn);
        modeWrap.appendChild(btn);
    });
    filterCard.appendChild(modeWrap);

    const pickerWrap = document.createElement("div");
    pickerWrap.className = "flex items-center gap-2";
    filterCard.appendChild(pickerWrap);

    const accSel = document.createElement("select");
    accSel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 ml-auto";
    const allOpt = document.createElement("option");
    allOpt.value = "";
    allOpt.textContent = t("reports.filter.allAccounts");
    accSel.appendChild(allOpt);
    _state.accounts.forEach((acc) => {
        const opt = document.createElement("option");
        opt.value = String(acc.id);
        opt.textContent = acc.name;
        accSel.appendChild(opt);
    });
    accSel.addEventListener("change", () => {
        _state.accountId = accSel.value ? parseInt(accSel.value) : null;
        const balCanvas = document.getElementById("canvas-balance");
        const balPh = document.getElementById("balance-placeholder");
        if (balCanvas) balCanvas.style.display = _state.accountId ? "" : "none";
        if (balPh) balPh.style.display = _state.accountId ? "none" : "";
        _loadAllCharts();
    });
    filterCard.appendChild(accSel);

    const dlAllBtn = document.createElement("button");
    dlAllBtn.textContent = t("reports.export.all");
    dlAllBtn.className = "text-sm text-gray-400 hover:text-indigo-400 transition-colors border border-gray-700 rounded-lg px-3 py-2";
    dlAllBtn.addEventListener("click", () => {
        [
            ["donut", "expenses-by-category.png"],
            ["trend", "monthly-trend.png"],
            ["balance", "balance-history.png"],
            ["sollIst", "soll-ist.png"],
        ].forEach(([key, name]) => _downloadPng(key, name));
    });
    filterCard.appendChild(dlAllBtn);

    main.appendChild(filterCard);

    const grid = document.createElement("div");
    grid.className = "grid grid-cols-1 md:grid-cols-2 gap-6";
    grid.appendChild(_chartCard("canvas-donut", "reports.chart.expensesByCategory"));
    grid.appendChild(_chartCard("canvas-trend", "reports.chart.monthlyTrend"));
    grid.appendChild(_chartCard("canvas-balance", "reports.chart.balanceHistory", "balance-placeholder"));
    grid.appendChild(_chartCard("canvas-sollist", "reports.chart.sollIst"));
    main.appendChild(grid);

    app.appendChild(main);

    _setChartDefaults();
    _renderPickers(pickerWrap);
    await _loadAllCharts();
    fadeInUp(main);
}
