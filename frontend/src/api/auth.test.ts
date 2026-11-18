import { describe, expect, it } from "vitest";
import { parseAuthMe } from "./auth";

describe("parseAuthMe", () => {
  it("reads the SWA principal", () => {
    const p = parseAuthMe({
      clientPrincipal: {
        identityProvider: "aad",
        userId: "abc",
        userDetails: "me@outlook.com",
        userRoles: ["anonymous", "authenticated", "owner"],
      },
    });
    expect(p?.userId).toBe("abc");
    expect(p?.userRoles).toContain("owner");
  });

  it("returns null when signed out", () => {
    expect(parseAuthMe({ clientPrincipal: null })).toBeNull();
    expect(parseAuthMe(null)).toBeNull();
    expect(parseAuthMe({ clientPrincipal: { userRoles: ["owner"] } })).toBeNull();
  });
});
