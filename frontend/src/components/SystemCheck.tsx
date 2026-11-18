import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import { pollUntil } from "../api/poll";
import type { Check, DurableStart, DurableStatus, HealthResponse, MeResponse } from "../api/types";

type Row = { label: string; state: "pending" | "ok" | "fail"; detail: string };

const TERMINAL = new Set(["Completed", "Failed", "Terminated"]);

const errorText = (e: unknown) =>
  e instanceof ApiError ? `${e.message} (${e.code})` : e instanceof Error ? e.message : String(e);

const fromCheck = (label: string, c: Check | undefined): Row =>
  c ? { label, state: c.ok ? "ok" : "fail", detail: c.detail } : { label, state: "fail", detail: "Not reported" };

/** M0 foundation check: identity reaches the API, managed identity reaches
 *  Storage and Key Vault, providers resolve, and Durable Functions runs. */
export function SystemCheck() {
  const [rows, setRows] = useState<Row[]>([]);
  const [build, setBuild] = useState<string>("");
  const [durable, setDurable] = useState<Row>({
    label: "Durable Functions",
    state: "pending",
    detail: "Not run yet",
  });
  const [durableRunning, setDurableRunning] = useState(false);

  const runChecks = useCallback(async () => {
    setRows([{ label: "API", state: "pending", detail: "Checking…" }]);
    const next: Row[] = [];
    try {
      const me = await api.get<MeResponse>("/api/me");
      next.push({ label: "Sign-in reaches API", state: "ok", detail: `ownerId ${me.ownerId}` });
    } catch (e) {
      next.push({ label: "Sign-in reaches API", state: "fail", detail: errorText(e) });
    }
    try {
      const health = await api.get<HealthResponse>("/api/health");
      applyHealth(health, next);
    } catch (e) {
      // 503 still carries the health body; show its checks.
      if (e instanceof ApiError && e.status === 503 && e.body) {
        applyHealth(e.body as HealthResponse, next);
      } else {
        next.push({ label: "Health", state: "fail", detail: errorText(e) });
      }
    }
    setRows(next);

    function applyHealth(h: HealthResponse, out: Row[]) {
      out.push(fromCheck("Blob Storage", h.checks.storage));
      out.push(fromCheck("Key Vault", h.checks.keyVault));
      out.push(fromCheck("Providers", h.checks.providers));
      const b = h.build;
      setBuild([b.version, b.gitSha?.slice(0, 7), b.builtAt].filter(Boolean).join(" · "));
    }
  }, []);

  const runDurable = useCallback(async () => {
    setDurableRunning(true);
    setDurable((d) => ({ ...d, state: "pending", detail: "Starting orchestration…" }));
    try {
      const { instanceId } = await api.post<DurableStart>("/api/health/durable");
      const status = await pollUntil(
        async () => {
          const s = await api.get<DurableStatus>(`/api/health/durable/${encodeURIComponent(instanceId)}`);
          setDurable((d) => ({ ...d, detail: `${s.runtimeStatus}…` }));
          return s;
        },
        (s) => TERMINAL.has(s.runtimeStatus),
        { intervalMs: 1500, timeoutMs: 90_000 },
      );
      const ok = status.runtimeStatus === "Completed" && status.output === "pong";
      setDurable((d) => ({
        ...d,
        state: ok ? "ok" : "fail",
        detail: `${status.runtimeStatus}, output ${JSON.stringify(status.output)}`,
      }));
    } catch (e) {
      setDurable((d) => ({ ...d, state: "fail", detail: errorText(e) }));
    } finally {
      setDurableRunning(false);
    }
  }, []);

  useEffect(() => {
    void runChecks();
  }, [runChecks]);

  return (
    <section className="card">
      <div className="card-head">
        <h2>System check</h2>
        <button className="btn btn-ghost" onClick={() => void runChecks()}>
          Re-run
        </button>
      </div>
      <ul className="checks">
        {[...rows, durable].map((r) => (
          <li key={r.label} className={`check check-${r.state}`}>
            <span className="dot" aria-hidden />
            <span className="check-label">{r.label}</span>
            <span className="check-detail">{r.detail}</span>
          </li>
        ))}
      </ul>
      <div className="card-foot">
        <button className="btn" onClick={() => void runDurable()} disabled={durableRunning}>
          {durableRunning ? "Running…" : "Run Durable check"}
        </button>
        {build && <span className="muted small">Backend {build}</span>}
      </div>
    </section>
  );
}
