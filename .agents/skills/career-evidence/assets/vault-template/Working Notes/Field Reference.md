# Field Reference

Generated from the skill's `scripts/schema.py` — do not edit by hand; regenerate with `python scripts/export_index.py --write-field-reference`.

These are the values the tools accept in note frontmatter. Anything outside these lists is flagged by the vault audit.

## Application

### status

- `discovered`
- `researching`
- `preparing`
- `applied`
- `screening`
- `interviewing`
- `offer`
- `rejected`
- `withdrawn`
- `closed`

### discovery_method

- `formal-referral`
- `informal-referral`
- `recruiter-outreach`
- `job-board`
- `company-site`
- `professional-network`
- `word-of-mouth`
- `event`
- `other`
- `unknown`

### compensation_status

- `listed-in-posting`
- `provided-by-recruiter`
- `discussed-in-interview`
- `not-listed-in-captured-posting`
- `unknown`

### compensation_period

- `hourly`
- `monthly`
- `annual`
- `unknown`

### work_model

- `onsite`
- `hybrid`
- `remote`
- `unknown`

## People

### job-search role (`relationships`)

- `formal-referral`
- `informal-referral`
- `internal-contact`
- `recruiter`
- `hiring-manager`
- `interviewer`
- `scheduler`
- `other`

### professional relationship

- `current-coworker`
- `former-coworker`
- `current-team-lead`
- `former-team-lead`
- `current-manager`
- `former-manager`
- `current-director`
- `former-director`
- `current-direct-report`
- `former-direct-report`
- `mentor`
- `mentee`
- `client`
- `vendor`
- `professional-peer`
- `other`

### reference permission (`reference_status`)

- `confirmed`
- `requested`
- `prospective`
- `declined`

### contact audience

- `self`
- `application`
- `recruiter`
- `public`

## Interviews

### stage

- `recruiter-screen`
- `hiring-manager`
- `technical-screen`
- `take-home`
- `technical-panel`
- `system-design`
- `behavioral`
- `onsite`
- `final`
- `other`

### method

- `phone`
- `video`
- `onsite`
- `async`
- `unknown`

## Evidence

### role status

- `needs-interview`
- `source-verified`
- `documented`

### accomplishment status

- `draft`
- `partial`
- `verified`

### claim class

- `exact`
- `approved-estimate`
- `derived`
- `qualitative`
- `unknown`

## Submission

### submission status

- `draft`
- `ready`
- `submitted`
- `confirmed`
