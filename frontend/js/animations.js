function expoOut(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

export function countUp(el, targetStr, duration = 700) {
    const target = parseFloat(targetStr);
    if (isNaN(target)) { el.textContent = targetStr; return; }
    const start = performance.now();
    const abs = Math.abs(target);
    const sign = target < 0 ? "-" : target > 0 ? "+" : "";

    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        const val = expoOut(p) * abs;
        el.textContent = `${sign}${val.toFixed(2).replace(".", ",")} €`;
        if (p < 1) requestAnimationFrame(tick);
        else el.textContent = `${sign}${abs.toFixed(2).replace(".", ",")} €`;
    }
    requestAnimationFrame(tick);
}

export function animateProgressBars(container) {
    const bars = container.querySelectorAll("[data-pct]");
    bars.forEach((bar, i) => {
        const pct = Math.min(parseFloat(bar.dataset.pct) || 0, 100);
        bar.style.width = "0%";
        setTimeout(() => {
            bar.style.transition = "width 0.6s cubic-bezier(0.16,1,0.3,1)";
            bar.style.width = `${pct}%`;
        }, i * 30);
    });
}

export function fadeInUp(elements, stagger = 30) {
    const els = elements instanceof NodeList ? Array.from(elements) : [elements];
    els.forEach((el, i) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(12px)";
        el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
        setTimeout(() => {
            el.style.opacity = "1";
            el.style.transform = "translateY(0)";
        }, i * stagger);
    });
}

export async function crossfade(el, loadFn) {
    el.style.transition = "opacity 0.18s ease, transform 0.18s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-6px)";
    await new Promise(r => setTimeout(r, 200));
    await loadFn();
    el.style.transform = "translateY(6px)";
    requestAnimationFrame(() => {
        el.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
    });
}
