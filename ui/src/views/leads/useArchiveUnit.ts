import { useCallback } from "react";
import { api } from "../../api/client";
import { useModal } from "../../components/Modal";
import { useToast } from "../../components/Toast";

/** `archiveUnit()` (index.html:1527): a reason modal, then `/api/archive`. The
 *  modal itself refreshes the index on a successful submit. */
export function useArchiveUnit() {
  const modal = useModal();
  const toast = useToast();

  return useCallback(
    (kind: string, path: string, label: string) => {
      void modal(
        [{ key: "reason", label: "Why (optional, kept on the note)", multiline: true }],
        {
          title: `Archive ${label}?`,
          submit: "Archive",
          onSubmit: async (values) => {
            await api("/api/archive", {
              method: "POST",
              body: { kind, path, reason: values.reason },
            });
            toast(`Archived ${label}`);
          },
        },
      );
    },
    [modal, toast],
  );
}
