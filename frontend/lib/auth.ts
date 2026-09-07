import type { AuthUser } from "./types";

const TOKEN_KEY = "harbordock_access_token";
const USER_KEY = "harbordock_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function isAdmin(user: AuthUser | null | undefined): boolean {
  return Boolean(user?.roles?.includes("admin"));
}

export function isCustomer(user: AuthUser | null | undefined): boolean {
  return Boolean(user?.roles?.includes("customer"));
}
