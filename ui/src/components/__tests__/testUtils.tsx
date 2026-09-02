import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactNode } from "react";
import { ToastProvider } from "../Toast";
import { ModalProvider } from "../Modal";
import { NoteOverlayProvider } from "../NoteOverlay";
import type { Schema } from "../../api/types";

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

export function renderWithProviders(
  ui: ReactNode,
  qc: QueryClient = makeQueryClient(),
): RenderResult {
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <NoteOverlayProvider>
          <ModalProvider>{ui}</ModalProvider>
        </NoteOverlayProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

/** Only the keys these tests touch; the rest of the schema is irrelevant here. */
export function schemaFixture(overrides: Partial<Schema> = {}): Schema {
  const empty: string[] = [];
  return {
    status: empty,
    terminal: empty,
    lead_status: ["open", "passed"],
    interview_status: empty,
    discovery_method: empty,
    compensation_status: empty,
    compensation_period: empty,
    work_model: empty,
    stage: empty,
    method: empty,
    contact_relationship: empty,
    professional_relationship: empty,
    people_folders: empty,
    reference_permission: empty,
    contact_audience: empty,
    editable: {},
    archivable: ["application", "lead"],
    vault_name: "Career",
    forms: {
      application: { title: "", submit: "", endpoint: "/api/application", fields: [] },
      person: { title: "", submit: "", endpoint: "/api/person", fields: [] },
      role: { title: "", submit: "", endpoint: "/api/role", fields: [] },
      accomplishment: {
        title: "",
        submit: "",
        endpoint: "/api/accomplishment",
        fields: [],
      },
      lead: {
        title: "Add a lead",
        submit: "Create",
        endpoint: "/api/lead",
        fields: [
          { name: "company", label: "Company", required: true },
          { name: "status", label: "Status", widget: "select", enum: "lead_status" },
        ],
      },
    },
    ...overrides,
  };
}
