import { login, register } from "../auth.js";
import { navigate } from "../router.js";
import { setLanguage, currentLanguage } from "../i18n.js";

export async function renderLogin() {
  const isRegister = window.location.hash === "#/register";
  const app = document.getElementById("app");

  const nameField = isRegister
    ? [
        '<div>',
        '  <label id="lbl-name" class="block text-sm text-gray-400 mb-1"></label>',
        '  <input id="name" type="text" required',
        '    class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5',
        '           text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500">',
        '</div>',
      ].join("\n")
    : "";

  app.innerHTML = [
    '<div class="min-h-screen bg-gray-950 flex items-center justify-center p-4">',
    '  <div class="w-full max-w-md">',
    '    <div class="flex justify-end mb-6">',
    '      <button id="btn-de" class="text-sm px-3 py-1 rounded-l-lg border border-gray-700 bg-gray-800 text-gray-400 hover:text-white">DE</button>',
    '      <button id="btn-en" class="text-sm px-3 py-1 rounded-r-lg border border-gray-700 border-l-0 bg-gray-800 text-gray-400 hover:text-white">EN</button>',
    '    </div>',
    '    <div class="bg-gray-900 rounded-2xl border border-gray-800 p-8 shadow-2xl">',
    '      <h1 id="app-name" class="text-2xl font-bold text-white mb-1"></h1>',
    '      <p id="form-title" class="text-gray-400 text-sm mb-8"></p>',
    '      <div id="error-box" class="hidden mb-4 p-3 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm" role="alert"></div>',
    '      <form id="auth-form" class="space-y-4">',
    nameField,
    '        <div><label id="lbl-email" class="block text-sm text-gray-400 mb-1"></label>',
    '          <input id="email" type="email" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"></div>',
    '        <div><label id="lbl-password" class="block text-sm text-gray-400 mb-1"></label>',
    '          <input id="password" type="password" required minlength="12" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"></div>',
    '        <button type="submit" id="submit-btn" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-colors mt-2"></button>',
    '      </form>',
    '      <p class="text-center text-sm text-gray-500 mt-6">',
    '        <span id="switch-hint"></span>',
    '        <a id="switch-link" href="" class="text-indigo-400 hover:text-indigo-300 ml-1"></a>',
    '      </p>',
    '    </div>',
    '  </div>',
    '</div>',
  ].join("\n");

  // All text set via textContent — no user data in HTML string above
  document.getElementById("app-name").textContent = t("app.name");
  document.getElementById("form-title").textContent = t(isRegister ? "auth.registerTitle" : "auth.loginTitle");
  if (isRegister) document.getElementById("lbl-name").textContent = t("auth.name");
  document.getElementById("lbl-email").textContent = t("auth.email");
  document.getElementById("lbl-password").textContent = t("auth.password");
  document.getElementById("submit-btn").textContent = t(isRegister ? "auth.register" : "auth.login");
  document.getElementById("switch-hint").textContent = t(isRegister ? "auth.hasAccount" : "auth.noAccount");
  const switchLink = document.getElementById("switch-link");
  switchLink.textContent = t(isRegister ? "auth.switchToLogin" : "auth.switchToRegister");
  switchLink.href = isRegister ? "#/login" : "#/register";

  const lang = currentLanguage();
  ["de", "en"].forEach((l) => {
    const btn = document.getElementById(`btn-${l}`);
    if (l === lang) {
      btn.classList.replace("text-gray-400", "text-white");
      btn.classList.add("bg-indigo-600");
    }
    btn.addEventListener("click", () => setLanguage(l));
  });

  document.getElementById("auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("error-box");
    errorBox.classList.add("hidden");
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const nameEl = document.getElementById("name");
    try {
      if (isRegister) await register(email, password, nameEl?.value ?? "");
      await login(email, password);
      navigate("#/dashboard");
    } catch (err) {
      const key = `errors.${err.message}`;
      const msg = t(key) !== key ? t(key) : t("errors.generic");
      errorBox.textContent = msg;
      errorBox.classList.remove("hidden");
    }
  });
}
