import { useCallback } from "react";
import { api } from "../api/client";
import { useSchemaQuery } from "../api/queries";
import type { CreatedPath, FormKey, VocabularyKey } from "../api/types";
import { useModal } from "./Modal";
import { useToast } from "./Toast";

/** Scaffold forms come from `/api/schema` `forms`, so the field lists and their
 *  vocabularies live in schema.py rather than here (`formModal()`,
 *  index.html:1613). */
export type OpenFormModal = (key: FormKey) => Promise<CreatedPath | null>;

export function useFormModal(): OpenFormModal {
  const modal = useModal();
  const toast = useToast();
  const schema = useSchemaQuery();

  return useCallback<OpenFormModal>(
    async (key) => {
      const vocabularies = schema.data;
      const spec = vocabularies?.forms[key];
      if (!vocabularies || !spec) {
        toast("The schema has not loaded yet.", "error");
        return null;
      }
      let created: CreatedPath | null = null;

      await modal(
        spec.fields.map((field) => ({
          key: field.name,
          label: field.label,
          options: field.enum
            ? vocabularies[field.enum as VocabularyKey]
            : undefined,
          type: field.widget === "date" ? "date" : undefined,
          multiline: field.widget === "textarea",
          placeholder: field.placeholder,
        })),
        {
          title: spec.title,
          submit: spec.submit,
          onSubmit: async (values) => {
            for (const field of spec.fields)
              if (field.required && !values[field.name])
                throw new Error(`${field.label} is required.`);
            created = await api<CreatedPath>(spec.endpoint, {
              method: "POST",
              body: values,
            });
            toast(`Created ${created.path}`);
          },
        },
      );

      return created;
    },
    [modal, schema.data, toast],
  );
}
