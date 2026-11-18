import { describe, expect, it } from "vitest";
import { pollUntil, PollTimeoutError } from "./poll";

describe("pollUntil", () => {
  it("resolves once the status is done", async () => {
    let calls = 0;
    const result = await pollUntil(
      async () => ++calls,
      (n) => n >= 3,
      { intervalMs: 1, timeoutMs: 1000 },
    );
    expect(result).toBe(3);
  });

  it("times out", async () => {
    await expect(
      pollUntil(async () => "Running", () => false, { intervalMs: 5, timeoutMs: 20 }),
    ).rejects.toBeInstanceOf(PollTimeoutError);
  });
});
