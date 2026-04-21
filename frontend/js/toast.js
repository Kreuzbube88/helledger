let _container = null;

function _ensureContainer() {
    if (_container && document.body.contains(_container)) return _container;
    _container = document.createElement("div");
    _container.id = "toast-container";
    Object.assign(_container.style, {
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        zIndex: "9999",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        alignItems: "flex-end",
    });
    document.body.appendChild(_container);
    return _container;
}

export function toast(message, type = "success") {
    const container = _ensureContainer();
    const colors = {
        success: { bg: "rgba(16,185,129,0.15)", border: "rgba(16,185,129,0.4)", dot: "#10b981" },
        error:   { bg: "rgba(244,63,94,0.15)",  border: "rgba(244,63,94,0.4)",  dot: "#f43f5e" },
        info:    { bg: "rgba(99,102,241,0.15)",  border: "rgba(99,102,241,0.4)", dot: "#818cf8" },
    };
    const c = colors[type] ?? colors.info;

    const el = document.createElement("div");
    Object.assign(el.style, {
        background: c.bg,
        border: `1px solid ${c.border}`,
        color: "#e2e8f0",
        borderRadius: "0.75rem",
        padding: "0.75rem 1.25rem",
        fontSize: "0.875rem",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        maxWidth: "22rem",
        opacity: "0",
        transform: "translateY(8px)",
        transition: "opacity 0.25s ease, transform 0.25s ease",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        cursor: "pointer",
    });

    const dot = document.createElement("span");
    Object.assign(dot.style, {
        width: "6px", height: "6px", borderRadius: "50%",
        background: c.dot, flexShrink: "0",
    });

    const msg = document.createElement("span");
    msg.textContent = message;

    el.appendChild(dot);
    el.appendChild(msg);
    container.appendChild(el);

    requestAnimationFrame(() => {
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
    });

    const dismiss = () => {
        el.style.opacity = "0";
        el.style.transform = "translateY(8px)";
        setTimeout(() => el.remove(), 250);
    };
    el.addEventListener("click", dismiss);
    setTimeout(dismiss, 3500);
}

export function confirmDialog(message, onConfirm, confirmLabel) {
    const label = confirmLabel ?? (typeof t !== "undefined" ? t("transactions.delete") : "Löschen");

    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
        position: "fixed", inset: "0",
        background: "rgba(0,0,0,0.65)",
        backdropFilter: "blur(4px)", WebkitBackdropFilter: "blur(4px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: "10000", opacity: "0", transition: "opacity 0.2s ease",
    });

    const box = document.createElement("div");
    Object.assign(box.style, {
        background: "rgba(15,15,20,0.97)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "1.25rem",
        padding: "2rem",
        maxWidth: "24rem",
        width: "90%",
        transform: "scale(0.9) translateY(12px)",
        transition: "transform 0.3s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s ease",
        opacity: "0",
    });

    const msgEl = document.createElement("p");
    Object.assign(msgEl.style, {
        color: "#e2e8f0", marginBottom: "1.5rem",
        fontSize: "1rem", lineHeight: "1.5",
    });
    msgEl.textContent = message;

    const btns = document.createElement("div");
    btns.style.cssText = "display:flex;gap:0.75rem;justify-content:flex-end;";

    const cancelBtn = document.createElement("button");
    Object.assign(cancelBtn.style, {
        padding: "0.5rem 1.25rem", borderRadius: "0.5rem",
        border: "1px solid rgba(255,255,255,0.15)",
        background: "transparent", color: "#94a3b8",
        cursor: "pointer", fontSize: "0.875rem",
        transition: "background 0.15s",
    });
    cancelBtn.textContent = typeof t !== "undefined" ? t("transactions.cancel") : "Abbrechen";

    const confirmBtn = document.createElement("button");
    Object.assign(confirmBtn.style, {
        padding: "0.5rem 1.25rem", borderRadius: "0.5rem",
        border: "none", background: "rgba(244,63,94,0.9)",
        color: "white", cursor: "pointer",
        fontSize: "0.875rem", fontWeight: "500",
        transition: "background 0.15s",
    });
    confirmBtn.textContent = label;

    btns.appendChild(cancelBtn);
    btns.appendChild(confirmBtn);
    box.appendChild(msgEl);
    box.appendChild(btns);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
        overlay.style.opacity = "1";
        box.style.transform = "scale(1) translateY(0)";
        box.style.opacity = "1";
    });

    const close = () => {
        overlay.style.opacity = "0";
        box.style.transform = "scale(0.95) translateY(8px)";
        box.style.opacity = "0";
        setTimeout(() => overlay.remove(), 250);
    };

    cancelBtn.addEventListener("click", close);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    confirmBtn.addEventListener("click", () => { close(); onConfirm(); });
}
