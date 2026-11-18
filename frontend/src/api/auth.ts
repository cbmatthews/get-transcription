// Static Web Apps built-in auth. /.auth/me returns the signed-in principal.

export interface ClientPrincipal {
  identityProvider: string;
  userId: string;
  userDetails: string;
  userRoles: string[];
}

export const OWNER_ROLE = "owner";
export const LOGIN_URL = "/.auth/login/aad?post_login_redirect_uri=/";
export const LOGOUT_URL = "/.auth/logout?post_logout_redirect_uri=/";

export function parseAuthMe(body: unknown): ClientPrincipal | null {
  if (!body || typeof body !== "object") return null;
  const p = (body as { clientPrincipal?: unknown }).clientPrincipal;
  if (!p || typeof p !== "object") return null;
  const { identityProvider, userId, userDetails, userRoles } = p as Record<string, unknown>;
  if (typeof userId !== "string" || !userId) return null;
  return {
    identityProvider: typeof identityProvider === "string" ? identityProvider : "",
    userId,
    userDetails: typeof userDetails === "string" ? userDetails : "",
    userRoles: Array.isArray(userRoles) ? userRoles.filter((r): r is string => typeof r === "string") : [],
  };
}

export async function getPrincipal(): Promise<ClientPrincipal | null> {
  try {
    const res = await fetch("/.auth/me", { credentials: "same-origin" });
    if (!res.ok) return null;
    return parseAuthMe(await res.json());
  } catch {
    return null;
  }
}
