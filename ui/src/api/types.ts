/** Hand-written mirrors of the Python server's JSON payloads.
 *
 * These are the contract with `server/serve.py` and `server/export_index.py`:
 * when the server's shapes move and these do not, the UI stops compiling.
 * Optional-in-frontmatter fields are typed `string | null` because
 * `fm.get(...)` yields null, not an absent key. */

export interface ApplicationArtifact {
  name: string;
  path: string;
  bytes: number;
}

/** `Application Brief.md` frontmatter, projected by export_index.build(). The
 *  optional keys are schema.NOTE_TYPES["application"]["optional"]. */
export interface Application {
  company: string;
  position: string;
  status: string;
  active: boolean;
  path: string;
  brief: string;
  fingerprint: string;
  artifacts: ApplicationArtifact[];
  /** Document label ("Analysis", "Job Description", …) → vault-relative path. */
  notes: Record<string, string>;
  tags: string[];
  experience_level_synthesized?: string | null;
  job_url: string | null;
  posting_source: string | null;
  discovery_method: string | null;
  discovery_detail: string | null;
  date_found: string | null;
  date_applied: string | null;
  location: string | null;
  work_model: string | null;
  compensation_status: string | null;
  compensation_currency: string | null;
  compensation_min: string | null;
  compensation_max: string | null;
  compensation_period: string | null;
  compensation_requested: string | null;
  experience_level_stated: string | null;
  next_action: string | null;
  next_action_date: string | null;
  archived: string | null;
  archive_reason: string | null;
  archived_from: string | null;
}

export interface Lead {
  company: string | null;
  role: string | null;
  url: string | null;
  source: string | null;
  date_added: string | null;
  status: string | null;
  next_follow_up: string | null;
  passed_reason: string | null;
  application: string | null;
  path: string;
  fingerprint: string;
}

export interface ArchivedUnit {
  kind: "application" | "lead";
  company: string | null;
  position: string | null;
  status: string | null;
  archived: string | null;
  archive_reason: string | null;
  archived_from: string | null;
  path: string;
  brief: string;
  fingerprint: string;
}

/** One `## entry` of an application's Contacts.md, plus the fields parsed out
 *  of it. The field keys are free-form markdown, hence the index signature. */
export interface Contact {
  name: string;
  company: string;
  position: string;
  application: string;
  note: string;
  [field: string]: string | undefined;
}

export interface Interview {
  company: string;
  position: string;
  application: string;
  path: string;
  fingerprint: string;
  when: string;
  date: string;
  status: string;
  upcoming: boolean;
  stage: string | null;
  method: string | null;
  location_or_link: string | null;
  point_of_contact: string | null;
  interviewers: string | null;
  thank_you_sent: string | null;
  next_step: string | null;
}

/** A person's involvement in one application, from their "## Applications"
 *  entries; extra recorded fields ride along as strings. */
export interface PersonInvolvement {
  application: string;
  roles: string[];
  [field: string]: string | string[] | undefined;
}

export interface Person {
  name: string;
  folder: string | null;
  via: string | null;
  relationships: string[];
  professional_relationships: string[];
  company_context: string | null;
  reference_status: string | null;
  email: string | null;
  phone: string | null;
  preferred_contact_method: string | null;
  next_follow_up: string | null;
  last_contact: string | null;
  permission_confirmed: string | null;
  permission_confirmed_at: string | null;
  applications: PersonInvolvement[];
  path: string;
  fingerprint: string;
}

export interface EvidenceNote {
  kind: "role" | "accomplishment";
  title: string;
  company: string | null;
  role: string | null;
  status: string | null;
  skills: string[];
  themes: string[];
  path: string;
}

export interface SkillEvidence {
  kind: "role" | "accomplishment";
  title: string;
  company: string | null;
  path: string;
}

/** GET /api/index — export_index.build(). */
export interface VaultIndex {
  vault: string;
  vault_name: string;
  generated_note: string;
  applications: Application[];
  leads: Lead[];
  archived: ArchivedUnit[];
  contacts: Contact[];
  interviews: Interview[];
  people: Person[];
  evidence: EvidenceNote[];
  /** Skill name → the evidence notes that support it. */
  skills: Record<string, SkillEvidence[]>;
}

// -- /api/schema -----------------------------------------------------------

export interface SchemaFormField {
  name: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  widget?: "select" | "date" | "textarea";
  /** Names a flat vocabulary key in this same schema payload. */
  enum?: string;
}

export interface SchemaForm {
  title: string;
  submit: string;
  endpoint: string;
  fields: SchemaFormField[];
}

export type FormKey = "application" | "person" | "role" | "accomplishment" | "lead";

/** The flat string-list vocabularies; every key here is a valid `enum` target. */
export interface SchemaVocabularies {
  status: string[];
  terminal: string[];
  lead_status: string[];
  interview_status: string[];
  discovery_method: string[];
  compensation_status: string[];
  compensation_period: string[];
  work_model: string[];
  stage: string[];
  method: string[];
  contact_relationship: string[];
  professional_relationship: string[];
  people_folders: string[];
  reference_permission: string[];
  contact_audience: string[];
}

export interface Schema extends SchemaVocabularies {
  /** Note type → the frontmatter fields the dashboard may write. */
  editable: Record<string, string[]>;
  archivable: string[];
  forms: Record<FormKey, SchemaForm>;
  vault_name: string;
}

export type VocabularyKey = keyof SchemaVocabularies;

// -- notes, state, audit, jobs --------------------------------------------

export interface NotePayload {
  path: string;
  name: string;
  text: string;
  fingerprint: string;
  readonly: boolean;
}

export interface StateResponse {
  state: string;
}

export interface ResolveResponse {
  path: string;
}

export interface AuditReport {
  errors: string[];
  warnings: string[];
}

export type JobStatus =
  | { state: "running"; kind: string }
  | {
      state: "done";
      kind: string;
      pdf: string;
      preview: string | null;
      pages: number;
      notes: string[];
      problems: string[];
    }
  | { state: "failed"; kind: string; error: string };

// -- POST payloads ---------------------------------------------------------

export interface FieldSave {
  path: string;
  field: string;
  value: string;
  fingerprint?: string;
}

export interface FieldSaveResult {
  changed: boolean;
  fingerprint: string;
}

export interface NoteSave {
  path: string;
  text: string;
  fingerprint: string;
}

export interface NoteSaveResult {
  changed: true;
  fingerprint: string;
  warnings: string[];
}

export interface EntryAppend {
  path: string;
  heading?: string;
  title: string;
  fields: Record<string, string>;
}

export interface EntryAppendResult {
  changed: true;
  fingerprint: string;
}

export interface InterviewCreate {
  application: string;
  when: string;
  stage?: string;
  method?: string;
  location_or_link?: string;
  point_of_contact?: string;
  interviewers?: string;
}

/** Either a lead promotion (`lead`) or a fresh application. */
export type ApplicationCreate =
  | { lead: string }
  | {
      company: string;
      position: string;
      url?: string;
      discovery?: string;
      detail?: string;
      source?: string;
    };

export interface PersonCreate {
  name: string;
  folder?: string;
  professional_relationship?: string;
  relationship?: string;
  company_context?: string;
  email?: string;
  phone?: string;
}

export interface RoleCreate {
  company: string;
  title: string;
  start?: string;
  end?: string;
  team?: string;
}

export interface AccomplishmentCreate {
  company: string;
  title: string;
  role?: string;
  folder?: string;
}

export interface LeadCreate {
  company: string;
  role?: string;
  url?: string;
  source?: string;
  next_follow_up?: string;
}

/** Every scaffold route answers with the path it created. */
export interface CreatedPath {
  path: string;
}

export interface CaptureRequest {
  mode: "lead" | "application";
  company: string;
  url?: string;
  position?: string;
  text?: string;
  source?: string;
}

export type CaptureResult =
  | { path: string; mode: "lead"; stored_posting: false }
  | { path: string; mode: "application"; sha256: string };

export interface ArchiveRequest {
  kind: string;
  path: string;
  reason?: string;
  fingerprint?: string;
}

export interface ArchiveResult {
  changed: true;
  archived: string;
  from: string;
}

export interface UnarchiveRequest {
  path: string;
  fingerprint?: string;
}

export interface UnarchiveResult {
  changed: true;
  restored: string;
}

export interface RenderRequest {
  path: string;
  kind: string;
  pages?: number;
}

export interface RenderResult {
  job: string;
}
