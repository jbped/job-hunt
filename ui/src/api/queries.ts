import {
  useQuery,
  type QueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";
import { api } from "./client";
import type {
  AgentSessionList,
  AuditReport,
  Schema,
  VaultIndex,
} from "./types";

/** The three long-lived reads. The vanilla page refetched all three together
 *  (`refresh()`, index.html:427); here each is a query and a write invalidates
 *  the set, which is the same contract the server states: every non-render
 *  mutation rewrites the projection. */

export function useIndexQuery(): UseQueryResult<VaultIndex> {
  return useQuery({
    queryKey: ["index"],
    queryFn: () => api<VaultIndex>("/api/index"),
  });
}

export function useSchemaQuery(): UseQueryResult<Schema> {
  return useQuery({
    queryKey: ["schema"],
    queryFn: () => api<Schema>("/api/schema"),
  });
}

export function useAuditQuery(): UseQueryResult<AuditReport> {
  return useQuery({
    queryKey: ["audit"],
    queryFn: () => api<AuditReport>("/api/audit"),
  });
}

/** Call after any successful write. Renders are the one exception — they
 *  produce a PDF, not a note, and the server skips the reindex for them. */
export async function invalidateAfterWrite(qc: QueryClient): Promise<void> {
  await Promise.all([
    qc.invalidateQueries({ queryKey: ["index"] }),
    qc.invalidateQueries({ queryKey: ["schema"] }),
  ]);
  await qc.invalidateQueries({ queryKey: ["audit"] });
}

/** The chat's session list. Kept out of `invalidateAfterWrite`: an agent turn
 *  is not a vault write, and a vault write does not change this list. */
export function useAgentSessionsQuery(): UseQueryResult<AgentSessionList> {
  return useQuery({
    queryKey: ["agent-sessions"],
    queryFn: () => api<AgentSessionList>("/api/agent/sessions"),
  });
}
