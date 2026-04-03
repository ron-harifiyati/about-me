// frontend/assets/js/api.js

// Set this to your Lambda Function URL.
// For production, swap DEV_API_URL for PROD_API_URL.
const DEV_API_URL  = "https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com";
const PROD_API_URL = "https://o4o1xcb3wc.execute-api.us-east-1.amazonaws.com";

// Detect environment: if served from prod CloudFront domain, use prod API.
const API_BASE = (() => {
  const host = window.location.hostname;
  return (host === "dkdwnfmhg75yf.cloudfront.net")
    ? PROD_API_URL
    : DEV_API_URL;
})();

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function apiFetch(path, options = {}) {
  const url = `${API_BASE.replace(/\/$/, "")}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };
  const config = { ...options, headers };
  if (config.body && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }
  try {
    const resp = await fetch(url, config);
    const json = await resp.json();
    return { ok: resp.ok, status: resp.status, data: json.data, error: json.error };
  } catch (err) {
    return { ok: false, status: 0, data: null, error: "Network error" };
  }
}

const api = {
  get:    (path)         => apiFetch(path, { method: "GET" }),
  post:   (path, body)   => apiFetch(path, { method: "POST",   body }),
  put:    (path, body)   => apiFetch(path, { method: "PUT",    body }),
  delete: (path)         => apiFetch(path, { method: "DELETE" }),
};
