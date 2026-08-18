---
name: new-person
description: Add a person to the job-hunt vault's People folder — a contact, recruiter, referrer, hiring manager, interviewer, or professional reference. Use whenever the user mentions a person relevant to their job search — someone offered a referral, a recruiter reached out, an interviewer was named, or someone agreed to be a reference.
argument-hint: <Full Name>
---

# New person

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded — it defines how the vault is found and the truth
and privacy rules.

One note per person, at `People/<Full Name>.md`, whatever their roles. Being a
referral on one application and a reference for another are relationships
recorded on that one note, never a second file. Check for an existing note
before creating one.

The frontmatter shape is the `Person` section of
[vault-schema.md](../career-evidence/references/vault-schema.md); accepted
`relationships` values live in `scripts/schema.py` and the vault's
`Working Notes/Field Reference.md`.

1. Record organisation, title, relationship, contact details, and preferred
   contact method. Use `Unknown` for anything unconfirmed — never infer an
   email, phone number, or title.
2. If the person belongs to an application, add a `## [[People/<Full Name>]]`
   entry to that application's `Contacts.md` holding only their role in this
   application, and list the application under the person's `## Applications`
   section. Both links, or the index cannot associate them.
3. Keep the role distinctions honest: formal referral, informal referral,
   internal contact, recruiter, hiring manager, interviewer, scheduling
   contact, and professional reference are different things. Someone willing to
   forward a resume has not agreed to take a call.
4. The reference fields (`reference_status`, `permission_confirmed`) exist only
   once the person is being considered as a reference, and `confirmed` only
   after explicit consent from the person. Log each reference request so nobody
   is surprised or overused.
5. Record last contact and the next follow-up date.
