const SUPPORTED = ["de", "en"];

export async function initI18n() {
  const stored = localStorage.getItem("helledger_lang") ?? "de";
  const lng = SUPPORTED.includes(stored) ? stored : "de";
  const translations = await fetch(`/locales/${lng}.json`).then((r) => r.json());
  await i18next.init({
    lng,
    fallbackLng: "de",
    resources: { [lng]: { translation: translations } },
    interpolation: { escapeValue: true },
  });
  window.t = i18next.t.bind(i18next);
  document.documentElement.lang = lng;
}

export function setLanguage(lang) {
  if (!SUPPORTED.includes(lang)) return;
  localStorage.setItem("helledger_lang", lang);
  location.reload();
}

export function currentLanguage() { return i18next.language ?? "de"; }
