const ALLOWED_MEDIA_PROTOCOLS = new Set(["http:", "https:"]);

export function isSafeRelativeApiPath(path) {
  return typeof path === "string" && path.startsWith("/") && !path.startsWith("//");
}

export function sanitizeExternalUrl(value) {
  if (!value || typeof value !== "string") return "";

  try {
    const url = new URL(value, window.location.origin);
    if (!ALLOWED_MEDIA_PROTOCOLS.has(url.protocol)) return "";
    return url.href;
  } catch {
    return "";
  }
}
