---
name: leadspicker-master
description: >
  End-to-end Leadspicker pipeline: enrich, classify, personalize, and create outreach sequence
  in a single workflow. Use this skill whenever the user wants to prepare a Leadspicker project
  for outreach from scratch — for example "prepare project for outreach", "run full pipeline",
  "enrich and create sequence", "set up outreach for project 12345", "we sell X to Y, prepare
  the project", "priprav projekt na outreach", "spust celou pipeline", "priprav data a sekvenci",
  or any request that combines multiple Leadspicker steps (enrichment + classification +
  personalization + outreach) into one flow. Also triggers when the user describes their business
  and target audience alongside a Leadspicker project ID.
---

# Leadspicker Master Pipeline

Orchestrates 4 sub-skills into a single automated pipeline:
**Enrich → Classify → Personalize → Outreach Sequence**

The user describes their business and target persona once. The master handles everything else.

---

## Sub-Skill Files (Reference Material)

During execution, read these files for detailed API calls and prompt templates.
**Use ONLY the sections listed. IGNORE each sub-skill's "Workflow", "User Input", and "Suggested Next Steps" sections — follow THIS master flow instead.**

| Sub-skill | File | Sections to USE |
|-----------|------|----------------|
| Data Enrichment | `.claude/skills/leadspicker-data-enrichment/SKILL.md` | API endpoint, column types table, dependency map, recommended pipelines |
| Classifier | `.claude/skills/leadspicker-classifier/SKILL.md` | API Calls, Prompt Examples, Smart Variable Selection, Output Mode Decision, Prompt Writing Guidelines |
| Personalizer | `.claude/skills/leadspicker-personalizer/SKILL.md` | Prompt Templates, Language-Specific Templates, Multi-Language System, Smart Variable Selection |
| Outreach | `.claude/skills/leadspicker-outreach/SKILL.md` | Sequence API, Step Types, BASHO Framework, Message Generation, Variable Priority |

---

## Phase 0: Collect Input

Collect ALL parameters in a single conversation turn. Ask for everything at once:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `project_id` | Yes | Leadspicker project ID | `29841` |
| `api_key` | Yes | API key (confirm last 6 chars only) | `fd1f0d98...` |
| Business description | Yes | What you sell, what problem you solve | "AI-powered sales automation for B2B" |
| Target persona | Yes | Who to target — position + company type | "CEOs and VPs of Sales at SaaS companies" |
| Target countries | No | Countries to filter by (skip = no filter) | "Czech Republic, Slovakia, Germany" |
| Company size | No | Min/max employee count (skip = no filter) | "more than 10", "50-500 employees" |
| Language | Yes | Output language for hooks and messages | "Czech" / "English" / "German" |
| Sender name | Yes | Real name for LinkedIn messages | "Tomas" |
| LinkedIn Premium? | Yes | Determines InMail + connection request text | yes / no |

**If any parameter is missing, ask for ALL missing ones in a single follow-up — not one by one.**

Load the API key from `credentials/leadspicker.json` if available. Read the file first.

---

## Phase 1: Data Enrichment

**Goal:** Populate all data columns the pipeline needs for classification, personalization, and outreach.

Read `.claude/skills/leadspicker-data-enrichment/SKILL.md` sections "API Calls" and "Enrichment Column Types" for the exact API call format.

### API Endpoint

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
Headers: accept: application/json, content-type: application/json, x-api-key: {api_key}
```

### Execution Order

Launch columns in dependency order. 1-second delay between each API call.

**Batch 1 — Core Identity (no prerequisites):**

| Column | `magic_column_type` | `column_name` |
|--------|-------------------|---------------|
| Company Name | `company_name` | `Company Name` |
| Company Website | `company_website` | `Company Website` |
| Company LinkedIn | `company_linkedin` | `Company LinkedIn` |
| Person LinkedIn | `person_linkedin` | `Person LinkedIn` |
| Full Name | `li_full_name` | `Full Name` |
| Position | `person_position` | `Position` |

**Batch 2 — Company Deep (needs Company LinkedIn + Website):**

| Column | `magic_column_type` | `column_name` |
|--------|-------------------|---------------|
| Company Description | `li_company_description` | `LinkedIn Company Description` |
| Website Summary | `website_text_summary` | `Company Website Summary` |
| Company Size | `li_company_size` | `Company Size` |
| Company Country | `li_company_country` | `Company Country` |
| Founded Year | `company_founded_year` | `Founded Year` |
| Employee Count | `li_company_employee_count` | `Employee Count` |

**Batch 3 — Person Deep (needs Person LinkedIn):**

| Column | `magic_column_type` | `column_name` |
|--------|-------------------|---------------|
| About Me | `li_about_me` | `LinkedIn About Me` |
| Present Experience | `present_experience` | `Present Experience` |
| City | `li_city` | `City` |
| Country | `person_country` | `Person Country` |

> **NOTE:** `LinkedIn Latest Posts` (`li_latest_posts`) is NOT included by default. Only enrich it when the user explicitly requests icebreaker/personalization from LinkedIn posts. It's expensive and useless if not used in outreach messages.

**Batch 4 — Email:**

| Column | `magic_column_type` | `column_name` |
|--------|-------------------|---------------|
| Find Emails | `enrich_emails` | `Enrich Emails` |
| Validate Emails | `validate_emails` | `Validate Emails` |

### Request Body (per column)

```json
{
  "magic_column_type": "{type_from_table}",
  "column_name": "{name_from_table}"
}
```

### After Launching

Report summary:
> "Enrichment launched: {N} columns across 4 batches. Leadspicker processes these asynchronously — it takes a few minutes. Check your project in Leadspicker. When you see data appearing in the columns, come back and say **'continue'** to proceed with classification."

### CHECKPOINT 1: Wait for user to return

Do NOT poll or retry. The user checks Leadspicker UI and returns when ready.

---

## Phase 2: Position Classification (2 columns)

**Goal:** Score contacts by job title relevance, then create a boolean filter column.

Read `.claude/skills/leadspicker-classifier/SKILL.md` sections "API Calls" and "Prompt Writing Guidelines" for format details.

### Column 2a: Position Relevance (Scored)

Extract position criteria from the user's **target persona** input. Build a scored string classifier:

```
Determine whether this person holds a position relevant for outreach selling {BUSINESS_DESCRIPTION},
rate your confidence on a scale of 1-10, and provide a one-sentence reasoning.

A relevant position includes: {EXTRACT_FROM_TARGET_PERSONA — e.g., CEO, CTO, VP of Sales,
Head of Sales, Sales Director, Chief Revenue Officer, Founder, Co-Founder, Managing Director,
and similar leadership/decision-making roles in sales, revenue, or general management}.

Do NOT classify as relevant: {AUTO_GENERATE_EXCLUSIONS — e.g., individual contributors,
specialists, analysts, coordinators, assistants, interns, junior roles, or roles in
unrelated departments like design, HR, legal, unless the target persona specifically
includes them}.

Return your answer in this exact format: "Yes | score | reasoning" or "No | score | reasoning"
where score is a number from 1 (very uncertain) to 10 (absolutely certain), and reasoning
is one sentence explaining your decision.

If there is not enough information, return "No | 1 | Not enough data to determine."

Input:
- Position: {{position}}
```

**Settings:**
- `is_boolean: false`
- `column_name: "Position Relevance"`
- `magic_column_type: "ai_custom_column"`

### Column 2b: Is Relevant Position (Boolean — derived from 2a)

This column reads the output of "Position Relevance" and converts it to a simple boolean.
**Launch AFTER Column 2a has finished processing.**

```
You are given the result of a previous classification that determined whether a person's
position is relevant for outreach. The result is in the format "Yes | score | reasoning"
or "No | score | reasoning".

Answer yes ONLY if the answer starts with "Yes" AND the score is 7 or higher.
Answer no in all other cases (answer is "No", score is below 7, or data is missing/empty).

Input:
- Position Relevance: {{position_relevance}}
```

**Settings:**
- `is_boolean: true`
- `column_name: "Is Relevant Position"`
- `magic_column_type: "ai_custom_column"`

**Do NOT launch yet — preview in Phase 3 checkpoint.**

---

## Phase 3: Company Classification (2 columns)

**Goal:** Score companies for relevance, then create a boolean filter column.

### Column 3a: Company Relevance (Scored)

Derive company criteria from the user's **business description** and **target persona**. Build a scored string classifier:

```
Determine whether this company is a relevant prospect for {BUSINESS_DESCRIPTION},
rate your confidence on a scale of 1-10, and provide a one-sentence reasoning.

A relevant company: {DERIVE_FROM_BUSINESS_DESCRIPTION — e.g., "is a B2B company with
a sales team that does outbound prospecting, ideally SaaS or technology companies
with 50-500 employees"}.

Do NOT classify as relevant: {AUTO_GENERATE_EXCLUSIONS — e.g., "agencies, consultancies,
non-profits, government organizations, B2C-only companies, or companies with no
identifiable sales function"}.

Return your answer in this exact format: "Yes | score | reasoning" or "No | score | reasoning"
where score is a number from 1 (very uncertain) to 10 (absolutely certain), and reasoning
is one sentence explaining your decision.

If there is not enough information, return "No | 1 | Not enough data to determine."

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

**Settings:**
- `is_boolean: false`
- `column_name: "Company Relevance"`
- `magic_column_type: "ai_custom_column"`

### Column 3b: Is Relevant Company (Boolean — derived from 3a)

This column reads the output of "Company Relevance" and converts it to a simple boolean.
**Launch AFTER Column 3a has finished processing.**

```
You are given the result of a previous classification that determined whether a company
is a relevant prospect. The result is in the format "Yes | score | reasoning"
or "No | score | reasoning".

Answer yes ONLY if the answer starts with "Yes" AND the score is 7 or higher.
Answer no in all other cases (answer is "No", score is below 7, or data is missing/empty).

Input:
- Company Relevance: {{company_relevance}}
```

**Settings:**
- `is_boolean: true`
- `column_name: "Is Relevant Company"`
- `magic_column_type: "ai_custom_column"`

### CHECKPOINT 2: Preview Scored Classifications

Before launching, preview both **scored** prompts (2a + 3a) on the first 5 contacts.

**Step 1:** Show both scored prompts to the user for review.

**Step 2:** Submit both previews:
```
POST /projects/{project_id}/ai-prompt-preview/
```
Submit "Position Relevance" (is_boolean=false) and "Company Relevance" (is_boolean=false).

**Step 3:** Fetch contact data for context:
```
GET /projects/{project_id}/people?page=1&page_size=5
```

**Step 4:** Fetch preview results (wait a few seconds after submitting):
```
GET /projects/{project_id}/ai-prompt-preview/?column_name=Position Relevance&is_boolean=false
GET /projects/{project_id}/ai-prompt-preview/?column_name=Company Relevance&is_boolean=false
```

**Step 5:** Show combined preview table:

```
| Name | Position | Company | Company Website | Position Relevance | Company Relevance |
|------|----------|---------|-----------------|-------------------|-------------------|
| ... | ... | ... | ... | Yes/No | score | reason | Yes/No | score | reason |
```

**Step 6:** Ask for approval:
> "Do these scored classifications look correct? I can adjust the criteria if needed. Once approved, I'll launch both scored columns for all contacts."

- If approved → launch both scored columns (2a + 3a), then tell user:
  > "Scored classifications launched. When they finish processing, say **'continue'** and I'll launch the boolean filter columns (2b + 3b) that convert scores >= 7 to yes/no."
- If adjustments needed → modify prompts, re-preview
- If cancel → stop

### CHECKPOINT 2b: Launch Boolean Columns

After user confirms scored columns are processed:

1. Launch Column 2b ("Is Relevant Position") — reads `{{position_relevance}}`, answers yes if Yes + score >= 7
2. Launch Column 3b ("Is Relevant Company") — reads `{{company_relevance}}`, answers yes if Yes + score >= 7
3. If target countries were specified → launch Column 4 ("Is Target Country")
4. If company size was specified → launch Column 5 ("Is Target Size")
5. Proceed to Phase 4

### Column 4: Country Filter (Boolean — optional)

**Only create this column if the user specified target countries in Phase 0.**

This column checks both person country and company country against the target list.

```
Determine whether this contact is located in one of the target countries.

Target countries: {LIST_OF_TARGET_COUNTRIES}

Check both the person's country and the company's country. Answer yes if EITHER
the person's country OR the company's country matches one of the target countries.
Accept common variations and abbreviations (e.g., "Czech Republic" = "Czechia" = "CZ",
"United Kingdom" = "UK" = "Great Britain", "United States" = "US" = "USA").

Answer no if neither country matches, or if both fields are empty.

Input:
- Person Country: {{person_country}}
- Company Country: {{linkedin_company_country}}
```

**Settings:**
- `is_boolean: true`
- `column_name: "Is Target Country"`
- `magic_column_type: "ai_custom_column"`

### Column 5: Company Size Filter (Boolean — optional)

**Only create this column if the user specified a minimum/maximum company size in Phase 0.**

This column checks the employee count against the user's size criteria.

```
Determine whether this company meets the size requirement.

Size requirement: {SIZE_CRITERIA — e.g., "more than 10 employees", "between 50 and 500 employees", "fewer than 1000 employees"}

Check the employee count and company size information. Answer yes if the company
meets the size requirement. Accept various formats (e.g., "51-200", "501-1000",
numeric values like "150").

If the employee count is "1-10" or "Self-employed" and the minimum is higher, answer no.
If the data is empty or unclear, answer no.

Input:
- Employee Count: {{company_employee_count}}
- Company Size: {{linkedin_company_size}}
```

**Settings:**
- `is_boolean: true`
- `column_name: "Is Target Size"`
- `magic_column_type: "ai_custom_column"`

---

## Phase 4: Personalization

**Goal:** Create short personalization fragments for outreach messages.

Read `.claude/skills/leadspicker-personalizer/SKILL.md` sections "Prompt Templates" and "Language-Specific Templates" for the exact prompt text.

### Auto-Select Personalization Columns

Based on the language input, automatically determine which columns to create:

| Condition | Columns to Create |
|-----------|-------------------|
| **Always** | Website Hook |
| User wants icebreaker from LinkedIn posts | + Icebreaker (LinkedIn Posts) — **also enrich `li_latest_posts` first if not already enriched** |
| Language is NOT English | + Gender Title (standalone pane/paní, Herr/Frau, etc.) |
| Language is Czech, Polish, or Slovak | + First Name Vocative, + Last Name Vocative (no title prefix) |

> **IMPORTANT:** Only create the Icebreaker column if the user explicitly requests personalization from LinkedIn posts. When creating it, first check if `LinkedIn Latest Posts` has been enriched — if not, launch `li_latest_posts` enrichment first and wait for it to complete before creating the icebreaker column.

**IMPORTANT:** Salutations are always split into separate columns for maximum flexibility in outreach messages. Never use a single combined salutation column — always use Gender Title + Last Name Vocative as separate pieces.

### Column Details

**Website Hook:**
- Use the "Company Website Hook" template from personalizer skill
- Column name: `Website Hook` (or `Website Hook - {LANG}` if non-English)
- Variables: `{{company_name}}`, `{{website_text_summary}}`, `{{linkedin_company_description}}`
- For non-English: append `Write your output in {language}.` and use native opener

**Icebreaker:**
- Use the "LinkedIn Posts Icebreaker" template from personalizer skill
- Column name: `Icebreaker` (or `Icebreaker - {LANG}` if non-English)
- Variables: `{{linkedin_latest_posts}}`
- For non-English: append `Write your output in {language}.`

**Gender Title (non-English only):**
- Use the "Gender Title" template from personalizer skill
- Column name: `Gender Title - {LANG}` (e.g., `Gender Title - CZ`)
- Variables: `{{full_name}}`, `{{position}}`
- Outputs ONLY the title: "pane"/"paní" (CZ), "Herr"/"Frau" (DE), "Panie"/"Pani" (PL)
- Combined in outreach as: `{{gender_title_-_cz}} {{last_name_vocative_-_cz}}` → "pane Nováku"

**First Name Vocative (CZ/PL/SK only):**
- Use the language-specific vocative template from personalizer skill
- Column name: `{LANG} First Name Vocative`
- Variables: `{{first_name}}`

**Last Name Vocative (CZ/PL/SK only):**
- Use the language-specific vocative template from personalizer skill
- Column name: `{LANG} Last Name Vocative`
- Variables: `{{last_name}}`, `{{full_name}}`, `{{position}}`
- Outputs ONLY the declined last name — NO title prefix (pane/paní is in Gender Title column)

### CHECKPOINT 3: Preview Website Hook

**Step 1:** Show all personalization prompts to the user.

**Step 2:** Preview the Website Hook column (the most important one):
```
POST /projects/{project_id}/ai-prompt-preview/
GET /projects/{project_id}/ai-prompt-preview/?column_name={hook_column_name}&is_boolean=false
```

**Step 3:** Show preview table:

```
| Name | Company | Company Website | Website Hook |
|------|---------|-----------------|--------------|
| ... | ... | ... | "I saw your company helps..." |
```

**Step 4:** Ask for approval:
> "Here's how the website hooks look. If approved, I'll launch all {N} personalization columns."

- If approved → launch all personalization columns sequentially (1s delay between calls)
- If adjustments needed → modify, re-preview
- If cancel → stop

---

## Phase 5: Outreach Sequence

**Goal:** Create the outreach sequence with BASHO-framework messages.

Read `.claude/skills/leadspicker-outreach/SKILL.md` sections "Sequence API", "BASHO Framework", and "Message Generation" for all details.

### Auto-Suggest Sequence Type

| Available Data | Suggestion |
|---------------|------------|
| Email + LinkedIn enriched | Multi-channel (recommended) |
| Email only | Email sequence |
| LinkedIn only | LinkedIn sequence |

Ask the user:
> "I recommend a **{suggested_type}** sequence. Would you like to proceed with this, or prefer {alternatives}?"

### Pre-Sequence Checks

1. Check for existing sequence: `GET /sequence?project_id={project_id}`
   - If exists, warn user and ask if they want to delete it first
2. Fetch available columns: `GET /projects/{project_id}/people?page=1&page_size=5`
   - Identify which personalization variables are available
3. **Fetch boolean column header IDs** for condition gates: `GET /projects/{project_id}`
   - Look in `headers_data` for all columns where `is_boolean: true` and `id` is not null
   - These will be used as preconditions in the condition gate steps

### Variable Priority for Message Openers

Use the highest-priority available variable:

1. `{{icebreaker}}` — most personal (from LinkedIn posts)
2. `{{website_hook}}` — company-specific (from website)
3. `{{company_hook}}` — if exists
4. `{{experience_hook}}` — if exists
5. Manual opener using `{{position}}` + `{{company_name}}` — fallback

### Message Generation

Generate all messages following the BASHO framework from the outreach skill:

1. **Opener** — Use personalization variable (see priority above)
2. **Reframe** — Pattern interrupt question about the problem the user's product solves
3. **Proof** — Social proof referencing similar companies/outcomes
4. **CTA** — Low-friction next step

**Key rules:**
- Use the business description to craft relevant reframes and proof points
- Include 4-6 spintax locations per message
- Emails: HTML format, NO sender signature (Leadspicker appends it)
- LinkedIn: Plain text, ALWAYS include sender's real name at the end
- Follow word count limits from outreach skill (150-200 initial, 100-150 follow-up, 50-100 breakup)
- Subject line: 3-8 words, curiosity-driven, with spintax

### Show Messages for Approval

Display all generated messages with their step type, word count, and channel.
Wait for user approval before building the sequence.

### Build Sequence

**Step 1: Add boolean condition gates (ALWAYS do this first)**

Before any email or LinkedIn steps, add `magic_column_condition` steps at the beginning of the sequence. Each boolean filter column gets its own condition step, chained together.

1. Fetch boolean column header IDs from `GET /projects/{project_id}` → `headers_data` where `is_boolean: true`
2. Create one `magic_column_condition` step per boolean column, each with `preconditions: [column_header_id]`
3. Chain them: first condition is root (no parent), each subsequent condition uses `parent_relation: {"parent": previous_id, "relation_type": "yes"}`
4. The last condition's YES branch connects to the first email/message step

```python
# Example: 3 boolean columns
boolean_cols = [
    {"id": 380903, "name": "Is Relevant Position"},
    {"id": 380901, "name": "Is Relevant Company"},
    {"id": 380904, "name": "Is Target Size"},
]

prev_id = None
for i, col in enumerate(boolean_cols):
    data = {
        "outreach_step_type": "magic_column_condition",
        "is_reply": True, "subject": "", "message": "",
        "preconditions": [col["id"]],
        "position": {"x": 220, "y": 180 + (i * 170)},
    }
    if prev_id:
        data["parent_relation"] = {"parent": prev_id, "relation_type": "yes"}
    prev_id = create_step(data)

# Then chain the first email from the last condition's YES branch
email1 = create_step({
    ...,
    "parent_relation": {"parent": prev_id, "relation_type": "yes"},
})
```

**Step 2: Add email and LinkedIn steps**

Execute the rest of the sequence following the outreach skill's multi-channel structure.

**⚠️ MANDATORY: For ANY multi-channel sequence, ALWAYS use `first_degree_connection` check before LinkedIn steps.**

The multi-channel sequence MUST follow this branching structure after condition gates:

```
EMAIL 1 (is_reply=false)
  → DELAY 3d
    → FIRST_DEGREE_CONNECTION (check if already connected)
      ├── YES (already connected):
      │   → LI MSG (direct message)
      │     → DELAY 3d → EMAIL 2 → DELAY 5d → EMAIL 3
      │
      └── NO (not connected):
          → CONNECT (send connection request)
            → AFTER_CONNECTION (wait 7d for acceptance)
              ├── YES (accepted):
              │   → LI MSG (message after acceptance)
              │     → DELAY 3d → EMAIL 2 → DELAY 5d → EMAIL 3
              │
              └── NO (not accepted):
                  → INMAIL (premium only) or EMAIL fallback
                    → DELAY 3d → EMAIL 2 → DELAY 5d → EMAIL 3
```

**Key rules:**
- `first_degree_connection` is a BRANCHING step — it only supports `yes` and `no` children, NOT default `""` children
- Each branch (YES connected, YES accepted, NO not accepted) must have its own copy of the follow-up email chain (Email 2, delays, Email 3)
- Chain steps via `parent_relation`
- Use correct `outreach_step_type` values (empty string for email, "delay", "first_degree_connection", "connect", "after_connection", "message", "inmail_message")
- Set correct positions for visual layout — use different x coordinates for branches

**NEVER skip the `first_degree_connection` check in multi-channel sequences.** Without it, you risk sending connection requests to people who are already connected, which looks unprofessional.

### Verify

After building: `GET /sequence?project_id={project_id}` — show the complete sequence tree.

---

## Error Handling

| Error | Resolution |
|-------|-----------|
| 401 Unauthorized | Verify API key with user |
| 404 Not Found | Verify project ID |
| 400 Bad Request | Check JSON formatting |
| 422 Unprocessable | Column name exists — use different name |
| 429 Rate Limit | Increase delay to 2-3 seconds |

---

## Security

- **Never log or display** the full API key — confirm only last 6 characters
- API key used only for Leadspicker API calls
- Show all AI prompts to user before executing
- Show all outreach messages to user before building sequence

---

## Pipeline Summary Template

After completing the full pipeline, show this summary:

```
Pipeline Complete for Project {project_id}

Enrichment: {N} columns launched (Batches 1-4)
Classification:
  - "Is Relevant Position" (boolean) — launched
  - "Company Relevance" (scored) — launched
Personalization:
  - {list of personalization columns created}
Outreach:
  - {sequence_type} sequence created ({N} steps)
  - Messages use: {{icebreaker/website_hook}} as primary opener

Next steps:
- Wait for all columns to finish processing in Leadspicker
- Review classified contacts — filter by "Is Relevant Position" = true and Company Relevance score >= 7
- Launch the sequence when ready
```
