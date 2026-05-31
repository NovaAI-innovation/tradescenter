const TOKEN_KEY = "tc_access_token";

export const session = {
  get: () => sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY),
  set: (value) => {
    sessionStorage.setItem(TOKEN_KEY, value);
    localStorage.removeItem(TOKEN_KEY);
  },
  clear: () => {
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY);
  },
};
