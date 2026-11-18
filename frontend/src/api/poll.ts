// Poll an async operation until it's done. Used for Durable Functions status
// now, and for job progress from M1 on.

export interface PollOptions {
  intervalMs?: number;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export class PollTimeoutError extends Error {
  constructor() {
    super("Timed out waiting for the operation to finish.");
    this.name = "PollTimeoutError";
  }
}

const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(signal.reason ?? new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });

export async function pollUntil<T>(
  fetchStatus: () => Promise<T>,
  isDone: (value: T) => boolean,
  { intervalMs = 1500, timeoutMs = 60_000, signal }: PollOptions = {},
): Promise<T> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    signal?.throwIfAborted();
    const value = await fetchStatus();
    if (isDone(value)) return value;
    if (Date.now() + intervalMs > deadline) throw new PollTimeoutError();
    await sleep(intervalMs, signal);
  }
}
