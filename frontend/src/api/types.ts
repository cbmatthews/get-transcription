// Response shapes from the backend (backend/prism/api).

export interface Check {
  ok: boolean;
  detail: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  env: string;
  build: { version?: string; gitSha?: string; builtAt?: string };
  checks: Record<string, Check>;
}

export interface MeResponse {
  ownerId: string;
  principal: {
    identityProvider: string;
    userId: string;
    userDetails: string;
    userRoles: string[];
  };
}

export interface DurableStart {
  instanceId: string;
}

export interface DurableStatus {
  instanceId: string;
  runtimeStatus: "Pending" | "Running" | "Completed" | "Failed" | "Terminated" | "ContinuedAsNew" | string;
  output: unknown;
}
