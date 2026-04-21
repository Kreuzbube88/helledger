import { isAuthenticated } from "./auth.js";

const _routes = {};

export function route(hash, handler) { _routes[hash] = handler; }

export function navigate(hash) { window.location.hash = hash; }

export function initRouter() {
  async function handle() {
    const hash = window.location.hash || "#/login";
    const authed = isAuthenticated();
    if (hash !== "#/login" && hash !== "#/register" && !authed) { navigate("#/login"); return; }
    if ((hash === "#/login" || hash === "#/register") && authed) { navigate("#/dashboard"); return; }
    const handler = _routes[hash];
    if (handler) await handler();
    else navigate(authed ? "#/dashboard" : "#/login");
  }
  window.addEventListener("hashchange", handle);
  handle();
}
