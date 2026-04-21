const API_BASE = "/api";
let _token = localStorage.getItem("helledger_token") ?? null;

export function setToken(t) {
  _token = t;
  t ? localStorage.setItem("helledger_token", t) : localStorage.removeItem("helledger_token");
}

export function getToken() { return _token; }

async function _request(method, path, body, retry = true) {
  const headers = { "Content-Type": "application/json" };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: "include",
    body: body != null ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && retry) {
    const ok = await _tryRefresh();
    if (ok) return _request(method, path, body, false);
  }
  return res;
}

async function _tryRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, { method: "POST", credentials: "include" });
    if (!res.ok) return false;
    const { access_token } = await res.json();
    setToken(access_token);
    return true;
  } catch { return false; }
}

export const api = {
  get: (path) => _request("GET", path, null),
  post: (path, body) => _request("POST", path, body),
  patch: (path, body) => _request("PATCH", path, body),
  delete: (path) => _request("DELETE", path, null),
};
