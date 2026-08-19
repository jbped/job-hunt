---
name: new-person
description: Add a professional connection to the job-hunt vault's People folder — a coworker, team lead, manager, director, direct report, mentor, client, contact, recruiter, referrer, interviewer, or professional reference. Use whenever the user mentions a person relevant to their career or job search.
---

# New person

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded — it defines how the vault is found and the truth
and privacy rules.

One note per person, at `People/<Folder>/<Full Name>.md`, whatever their roles.
The folder files by relationship warmth and a person gets exactly one:
`Network/` for anyone the user has a real relationship with (coworkers past and
present, managers, mentors, friends, family), `Recruiters/` for agency and
in-house recruiters, `Job Hunt/` for everyone who exists in the vault because
of the search — networking targets, interviewers, hiring managers, company
contacts. When in doubt ask "could the user plausibly ask this person for a
favor?" — yes means `Network/`. Move a note (and update links to it) only when
the relationship itself changes, such as a cold contact becoming a real
connection.

Keep how the person worked with the user in `professional_relationships`,
job-search roles in `relationships`, and role in one application on that
application's entry. Being a former manager, a referral, and a reference can
all be true without collapsing those facts into one label. Check for an
existing note anywhere under `People/` before creating one.

The frontmatter shape is the `Person` section of
[vault-schema.md](../career-evidence/references/vault-schema.md); accepted
`relationships` and `professional_relationships` values live in
`scripts/schema.py` and the vault's `Working Notes/Field Reference.md`.

1. Record organisation, title, professional relationship, job-search role when
   there is one, contact details, and preferred contact method. Use `Unknown`
   for anything unconfirmed — never infer an email, phone number, title, or
   reporting relationship.
2. If the person belongs to an application, add a
   `## [[People/<Folder>/<Full Name>]]` entry to that application's
   `Contacts.md` holding only their role in this application, and list the
   application under the person's `## Applications` section. Both links, or the
   index cannot associate them.
3. Keep both sets of distinctions honest. Coworker, team lead, manager,
   director, direct report, mentor, and client describe professional history;
   formal referral, recruiter, hiring manager, interviewer, and scheduling
   contact describe job-search involvement. Professional-reference consent is
   separate from both. Someone willing to forward a resume has not agreed to
   take a call.
4. For networking chains, use `networking-target` for the person the user is
   trying to reach and `connector` for the person bridging the introduction,
   and set `via` on the target's note to a wikilink to the connector. The
   target files under `Job Hunt/`; the connector stays wherever the user's
   relationship with them puts them.
5. The reference fields (`reference_status`, `permission_confirmed`) exist only
   once the person is being considered as a reference, and `confirmed` only
   after explicit consent from the person. Log each reference request so nobody
   is surprised or overused.
6. Record last contact and the next follow-up date.
