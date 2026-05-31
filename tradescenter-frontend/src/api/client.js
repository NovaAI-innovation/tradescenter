import { appConfig } from "../config/appConfig";
import { isSafeRelativeApiPath } from "../security/url";
import { session } from "./session";

const API_BASE = appConfig.apiBaseUrl.replace(/\/$/, "");
const pathSegment = (value) => encodeURIComponent(String(value));
const querySuffix = (value = "") => {
  const query = String(value);
  if (!query) return "";
  if (!query.startsWith("?") || query.startsWith("??")) {
    throw new Error("Invalid query string");
  }
  return query;
};

async function request(path, options = {}) {
  if (!isSafeRelativeApiPath(path)) {
    throw new Error("Invalid API path");
  }

  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = session.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), appConfig.requestTimeoutMs);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (response.status === 401) {
    session.clear();
  }

  if (response.status === 204) return null;

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Request failed");
  }
  return payload;
}

export const authApi = {
  register: (input) => request("/auth/register", { method: "POST", body: JSON.stringify(input) }),
  login: (input) => request("/auth/login", { method: "POST", body: JSON.stringify(input) }),
  resendVerification: (input) =>
    request("/auth/verification/resend", { method: "POST", body: JSON.stringify(input) }),
  requestSmsOtp: (input) => request("/auth/otp/request", { method: "POST", body: JSON.stringify(input) }),
  verifyOtp: (input) => request("/auth/otp/verify", { method: "POST", body: JSON.stringify(input) }),
  requestPasswordRecovery: (input) =>
    request("/auth/password/recover", { method: "POST", body: JSON.stringify(input) }),
  me: () => request("/auth/me"),
  updateProfile: (input) => request("/auth/profile", { method: "PUT", body: JSON.stringify(input) }),
  logout: () => request("/auth/logout", { method: "POST" }),
};

export const socialApi = {
  feed: (params = "") => request(`/feed${querySuffix(params)}`),
  categories: () => request("/categories"),
  tags: () => request("/tags"),
  createPost: (input) => request("/posts", { method: "POST", body: JSON.stringify(input) }),
  getPost: (postId) => request(`/posts/${pathSegment(postId)}`),
  createComment: (postId, input) =>
    request(`/posts/${pathSegment(postId)}/comments`, { method: "POST", body: JSON.stringify(input) }),
  createReply: (commentId, input) =>
    request(`/comments/${pathSegment(commentId)}/replies`, { method: "POST", body: JSON.stringify(input) }),
  addReaction: (input) => request("/reactions", { method: "POST", body: JSON.stringify(input) }),
  removeReaction: (targetType, targetId, reactionType) => {
    const params = new URLSearchParams({
      target_type: String(targetType),
      target_id: String(targetId),
      reaction_type: String(reactionType),
    });

    return request(`/reactions?${params.toString()}`, {
      method: "DELETE",
    });
  },
  sharePost: (postId, input) =>
    request(`/posts/${pathSegment(postId)}/share`, { method: "POST", body: JSON.stringify(input) }),
};

export const profileAccessApi = {
  createRequest: (input) => request("/profile-access/requests", { method: "POST", body: JSON.stringify(input) }),
  listRequests: (params = "") => request(`/profile-access/requests${querySuffix(params)}`),
  respond: (requestId, action) =>
    request(`/profile-access/requests/${pathSegment(requestId)}/respond`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  allowed: (targetProfileId) => request(`/profile-access/allowed/${pathSegment(targetProfileId)}`),
};

export const messageApi = {
  getConversations: () => request("/messages/conversations"),
  createConversation: (input) =>
    request("/messages/conversations", { method: "POST", body: JSON.stringify(input) }),
  getMessages: (conversationId) => request(`/messages/conversations/${pathSegment(conversationId)}/messages`),
  sendMessage: (conversationId, input) =>
    request(`/messages/conversations/${pathSegment(conversationId)}/messages`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
};

export const tierApi = {
  status: () => request("/contractor/tier/status"),
  checkoutDemo: (targetTier) =>
    request("/contractor/tier/checkout-demo", {
      method: "POST",
      body: JSON.stringify({ target_tier: targetTier }),
    }),
};

export const billingApi = {
  status: () => request("/billing/subscription-status"),
  createCheckoutSession: (input) =>
    request("/billing/checkout-session", { method: "POST", body: JSON.stringify(input) }),
  createCustomerPortal: (input) =>
    request("/billing/customer-portal", { method: "POST", body: JSON.stringify(input) }),
};

export const verificationApi = {
  status: () => request("/verification/status"),
  createIdentitySession: (input) =>
    request("/verification/identity/session", { method: "POST", body: JSON.stringify(input) }),
};

export const discoveryApi = {
  indexedUsers: (params = "") => request(`/indexed-users${querySuffix(params)}`),
};

export const adminApi = {
  moderation: () => request("/admin/moderation"),
  action: (input) => request("/admin/moderation/action", { method: "POST", body: JSON.stringify(input) }),
};

export const healthApi = {
  health: () => request("/health"),
};

export { session };
