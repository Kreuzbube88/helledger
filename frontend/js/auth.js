import { api, setToken, getToken } from "./api.js";

export async function login(email, password) {
  const res = await api.post("/auth/login", { email, password });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "generic"); }
  const { access_token } = await res.json();
  setToken(access_token);
}

export async function register(email, password, name) {
  const res = await api.post("/auth/register", { email, password, name });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "generic"); }
  return res.json();
}

export async function logout() {
  await api.post("/auth/logout");
  setToken(null);
}

export async function getCurrentUser() {
  const res = await api.get("/auth/me");
  if (!res.ok) return null;
  return res.json();
}

export function isAuthenticated() { return !!getToken(); }
