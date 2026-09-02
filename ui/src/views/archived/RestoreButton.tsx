import { useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { invalidateAfterWrite } from "../../api/queries";
import type { ArchivedUnit, UnarchiveResult } from "../../api/types";
import { useToast } from "../../components/Toast";

/** `restoreUnit()` (index.html:1540): POST `/api/unarchive`, then refresh. */
export default function RestoreButton({ entry }: { entry: ArchivedUnit }) {
  const toast = useToast();
  const qc = useQueryClient();

  async function restore() {
    try {
      const result = await api<UnarchiveResult>("/api/unarchive", {
        method: "POST",
        body: { path: entry.path },
      });
      toast(`Restored to ${result.restored}`);
      await invalidateAfterWrite(qc);
    } catch (error) {
      toast(error instanceof Error ? error.message : String(error), "error");
    }
  }

  return (
    <button
      className="btn"
      onClick={() => void restore()}
      title={`Move back to ${entry.archived_from}`}
    >
      Restore
    </button>
  );
}
