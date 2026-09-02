/** The single fetch wrapper every call goes through — the port of `api()`
 *  (server/assets/ui/index.html:402). A POST carries the per-vault write token;
 *  a GET carries nothing, matching the server's own rule. */

const PLACEHOLDER = "__SESSION_TOKEN__";

/** The served page has the token substituted into an inline script — into the
 *  value only: serve.py replaces every occurrence of the literal, so the
 *  property it lands on is named `__CE_SESSION_TOKEN__` instead. Under
 *  `npm run dev` nothing substitutes it, so the placeholder survives and the
 *  token comes from the environment instead (VITE_SESSION_TOKEN, read from the
 *  vault's .cache/session-token). */
export function sessionToken(): string {
  const injected = window.__CE_SESSION_TOKEN__;
  if (injected && injected !== PLACEHOLDER) return injected;
  return import.meta.env.VITE_SESSION_TOKEN ?? PLACEHOLDER;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface ApiOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
}

export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const method = opts.method ?? "GET";
  const init: RequestInit = { method, signal: opts.signal };
  if (method === "POST") {
    init.headers = {
      "Content-Type": "application/json",
      "X-Session-Token": sessionToken(),
    };
    init.body = JSON.stringify(opts.body ?? {});
  }

  const response = await fetch(path, init);
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof body === "object" && body !== null && "error" in body
        ? String((body as { error: unknown }).error)
        : `${response.status} ${response.statusText}`;
    throw new ApiError(response.status, message);
  }
  return body as T;
}

/** Query-string helper: every read route takes exactly one parameter. */
export function withParam(path: string, key: string, value: string): string {
  return `${path}?${key}=${encodeURIComponent(value)}`;
}
