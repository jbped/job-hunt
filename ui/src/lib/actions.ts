import { useCallback } from "react";
import { api } from "../api/client";
import { useIndexQuery, useSchemaQuery } from "../api/queries";
import { useModal } from "../components/Modal";
import { useToast } from "../components/Toast";
import type { Application, CreatedPath } from "../api/types";
import { peopleFor } from "./people";

/** The vault's hand-built write actions — the modals the vanilla page did not
 *  drive from `/api/schema` `forms`, and which stay hand-built here. They live
 *  beside the views rather than inside one because the Applications rail and
 *  the Interviews view reach the same dialogs. The shared `useModal`
 *  invalidates the queries once a submit succeeds. */

/** `archiveUnit()`, index.html:1527. Resolves true once the archive is made. */
export function useArchiveApplication(): (app: Application) => Promise<boolean> {
  const modal = useModal();
  const toast = useToast();

  return useCallback(
    async (app) => {
      const label = `${app.company} — ${app.position}`;
      const values = await modal(
        [{ key: "reason", label: "Why (optional, kept on the note)", multiline: true }],
        {
          title: `Archive ${label}?`,
          submit: "Archive",
          onSubmit: async (entered) => {
            await api("/api/archive", {
              method: "POST",
              body: { kind: "application", path: app.path, reason: entered.reason },
            });
            toast(`Archived ${label}`);
          },
        },
      );
      return values !== null;
    },
    [modal, toast],
  );
}

/** `addContact()`, index.html:1637 — an entry appended to the application's
 *  own Contacts.md, not a People note. */
export function useAddContact(): (app: Application) => Promise<void> {
  const modal = useModal();
  const toast = useToast();
  const schema = useSchemaQuery();

  return useCallback(
    async (app) => {
      await modal(
        [
          { key: "title", label: "Full name" },
          { key: "organization_and_title", label: "Organization and title" },
          {
            key: "application_role",
            label: "Role in this application",
            options: schema.data?.contact_relationship,
          },
          { key: "relationship", label: "How you know them" },
          { key: "email", label: "Email" },
          { key: "phone", label: "Phone" },
          { key: "next_follow_up", label: "Next follow-up", type: "date" },
        ],
        {
          title: "Add a contact",
          submit: "Add",
          onSubmit: async (values) => {
            if (!values.title) throw new Error("A name is required.");
            const { title, ...fields } = values;
            await api("/api/entry", {
              method: "POST",
              body: { path: `${app.path}/Contacts.md`, title, fields },
            });
            toast("Contact added");
          },
        },
      );
    },
    [modal, schema.data, toast],
  );
}

/** `addInterview()`, index.html:1658. From the Applications rail the
 *  application is already in hand; from the Interviews view it is not, so the
 *  modal asks — active applications first, since that is almost always the
 *  answer. */
export function useAddInterview(): (app: Application | null) => Promise<void> {
  const modal = useModal();
  const toast = useToast();
  const schema = useSchemaQuery();
  const index = useIndexQuery();

  return useCallback(
    async (app) => {
      const applications = [...(index.data?.applications ?? [])].sort(
        (a, b) => Number(b.active) - Number(a.active),
      );
      const appField = app
        ? []
        : [
            {
              key: "application",
              label: "Application",
              choices: applications.map((a) => ({
                value: a.path,
                label: `${a.company} — ${a.position}`,
              })),
            },
          ];
      await modal(
        [
          ...appField,
          { key: "when", label: "Date and time", placeholder: "2026-09-02 14:00 MDT" },
          { key: "stage", label: "Stage", options: schema.data?.stage },
          { key: "method", label: "Method", options: schema.data?.method },
          { key: "point_of_contact", label: "Point of contact" },
          { key: "interviewers", label: "Interviewers" },
          { key: "location_or_link", label: "Location or link" },
        ],
        {
          title: "Schedule an interview",
          submit: "Schedule",
          onSubmit: async (values) => {
            if (!values.when) throw new Error("A date is required.");
            const { application, ...fields } = values;
            const appPath = app ? app.path : application;
            if (!appPath)
              throw new Error("Pick the application this interview belongs to.");
            const result = await api<CreatedPath>("/api/interview", {
              method: "POST",
              body: { application: appPath, ...fields },
            });
            toast(`Scheduled — preparation notes live in ${result.path}`);
          },
        },
      );
    },
    [index.data, modal, schema.data, toast],
  );
}

/** `linkPerson()`, index.html:1285 — records the involvement on the person's
 *  own note, which is where the one-note-per-person truth lives. */
export function useLinkPerson(): (app: Application) => Promise<void> {
  const modal = useModal();
  const toast = useToast();
  const schema = useSchemaQuery();
  const index = useIndexQuery();

  return useCallback(
    async (app) => {
      const people = index.data?.people ?? [];
      const linked = new Set(peopleFor(people, app).map((p) => p.path));
      const candidates = people.filter((p) => !linked.has(p.path));
      await modal(
        [
          {
            key: "person",
            label: "Person",
            choices: [
              { value: "", label: "— pick a person —" },
              ...candidates.map((p) => ({ value: p.path, label: p.name })),
              { value: "__new__", label: "+ Create a new person" },
            ],
          },
          { key: "name", label: "New person's name (only when creating)" },
          {
            key: "role",
            label: "Role in this application",
            options: schema.data?.contact_relationship,
          },
          { key: "notes", label: "Notes", multiline: true },
        ],
        {
          title: `Link a person to ${app.company}`,
          submit: "Link",
          onSubmit: async (values) => {
            if (!values.role) throw new Error("Pick their role in this application.");
            let path = values.person;
            if (path === "__new__" || (!path && values.name)) {
              if (!values.name)
                throw new Error("A name is required to create a person.");
              const created = await api<CreatedPath>("/api/person", {
                method: "POST",
                body: { name: values.name },
              });
              path = created.path;
            }
            if (!path) throw new Error("Pick a person, or create a new one.");
            const fields: Record<string, string> = { roles: values.role };
            if (values.notes) fields.notes = values.notes;
            await api("/api/entry", {
              method: "POST",
              body: {
                path,
                heading: "## Applications",
                title: `${app.company} | ${app.position}`,
                fields,
              },
            });
            toast("Linked");
          },
        },
      );
    },
    [index.data, modal, schema.data, toast],
  );
}
