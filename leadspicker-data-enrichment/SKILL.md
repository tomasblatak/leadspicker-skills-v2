---
name: leadspicker-data-enrichment
description: >
  Orchestrates data preparation and enrichment for contacts in Leadspicker.com projects.
  Runs built-in enrichment columns (email finding, email validation, LinkedIn data, company website
  summaries, department headcounts) and AI-powered magic columns in the right sequence via REST API.
  Use this skill whenever the user wants to enrich, prepare, or augment contact data in Leadspicker —
  for example "obohat kontakty o emaily", "enrichni projekt o LinkedIn data", "prepare data for outreach",
  "add company info to my leads", "find emails for my contacts", "run full enrichment pipeline",
  or any request to add data columns to a Leadspicker project. Also triggers when the user mentions
  Leadspicker enrichment, data preparation, contact augmentation, or wants to run multiple enrichment
  steps in sequence. Even if the user just says "prepare my data" or "enrich my leads" in the context
  of Leadspicker, use this skill.
---

# Leadspicker Data Enrichment Orchestrator

Prepares and enriches contact data in Leadspicker projects by running built-in and AI-powered
enrichment columns via the magic-columns API.

This skill supports two modes:

1. **Selective mode** — The user names specific columns they want (e.g., "enrich LinkedIn
   company description and website summary"). Run only those columns, plus any prerequisites
   they depend on.
2. **Pipeline mode** — The user describes a goal (e.g., "prepare data for outreach"). Select
   and run a full recommended pipeline.

The enrichment runs server-side inside Leadspicker. Each API call creates a new column that
Leadspicker populates asynchronously for all contacts in the project.

---

## User Input

Always collect (or confirm you have) these parameters before making any API calls:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `project_id` | Leadspicker project ID | `26256` |
| `api_key` | User's API key (`x-api-key`) | `fd1f0d98...` |
| Enrichment request | Specific columns OR a goal | `"LinkedIn Company Description and Website Summary"` or `"prepare for outreach"` |

### How to interpret the user's request

**If the user names specific columns** (e.g., "enrich company description", "add website
summary", "get LinkedIn posts"):
→ Use **Selective mode**. Match their words to columns in the table below. Then check the
  Dependency Map and automatically include any prerequisite columns they haven't mentioned.
  Show the user what you'll run (requested + prerequisites) and confirm.

**If the user describes a goal** (e.g., "full enrichment", "prepare for outreach", "find emails"):
→ Use **Pipeline mode**. Pick the best matching pipeline from the Recommended Pipelines section.

**If it's ambiguous**, ask: "Do you want me to enrich just [specific columns], or run
a full [pipeline name] pipeline?"

---

## Dependency Map

Some columns need other columns to exist first (because they use that data as input).
When the user requests a column, automatically include its prerequisites.

```
No prerequisites (can run anytime):
  → Company Name (company_name)
  → Company Website (company_website)
  → Company LinkedIn Profile (company_linkedin)
  → Person LinkedIn Profile (person_linkedin)
  → Full Name (li_full_name)
  → Position (person_position)
  → Person Country (person_country)
  → LinkedIn Location (li_location)
  → LinkedIn City (li_city)
  → LinkedIn Company Size (li_company_size)
  → LinkedIn Company Country (li_company_country)
  → Company Founded Year (company_founded_year)
  → Company Employee Count (li_company_employee_count)
  → Enrich Emails (enrich_emails)
  → Is LinkedIn Premium (linkedin_premium)
  → Is First Degree Connection (is_first_degree_connection)
  → LinkedIn Followers (followers_count)
  → LinkedIn Skills (linkedin_skills)

Needs Person LinkedIn Profile (person_linkedin):
  → LinkedIn About Me (li_about_me)
  → LinkedIn Latest Posts (li_latest_posts)
  → Present Positions Summary (present_experience)
  → Past Positions Summary (past_experience)
  → Education Summary (education_summary)

Needs Company LinkedIn Profile (company_linkedin):
  → LinkedIn Company Description (li_company_description)
  → All Department Headcounts (li_company_people_*)

Needs Company Website (company_website):
  → Company Website Summary (website_text_summary)

Needs Enrich Emails (enrich_emails):
  → Validate Emails (validate_emails)
  → Email MX (email_mx)

Needs data from Batches 1-3 (for AI context):
  → All AI Custom Columns (classification, icebreakers, cleaning, etc.)
```

**Example — Selective mode resolution:**

User says: "I want LinkedIn Company Description and Company Website Summary"

1. LinkedIn Company Description needs → Company LinkedIn Profile
2. Company Website Summary needs → Company Website
3. Neither Company LinkedIn Profile nor Company Website have prerequisites

Result — run in this order:
- Batch 1: Company LinkedIn Profile + Company Website (prerequisites)
- Batch 2: LinkedIn Company Description + Company Website Summary (requested)

Always show this resolved plan to the user before executing.

---

## Available Enrichment Columns

All enrichments use the same API endpoint. Each creates a column with a specific output.
The `magic_column_type` is the exact value you must send in the API request body.
Built-in enrichments don't need a prompt, while AI columns do.

### Person Data (from LinkedIn)

| Column Name | `magic_column_type` | Variable | What It Does |
|-------------|---------------------|----------|--------------|
| Full Name | `li_full_name` | `{{full_name}}` | Extracts clean full name from LinkedIn |
| Position | `person_position` | `{{position}}` | Current job title |
| Person Country | `person_country` | `{{person_country}}` | Country from LinkedIn profile |
| LinkedIn Location | `li_location` | `{{linkedin_location}}` | Location string from LinkedIn |
| LinkedIn City | `li_city` | `{{linkedin_city}}` | City extracted from LinkedIn |
| LinkedIn About Me | `li_about_me` | `{{linkedin_about_me}}` | LinkedIn bio/summary section |
| LinkedIn Latest Posts | `li_latest_posts` | `{{linkedin_latest_posts}}` | Recent LinkedIn post content |
| Present Positions Summary | `present_experience` | `{{present_experiences}}` | Current roles summary |
| Past Positions Summary | `past_experience` | `{{past_experiences}}` | Previous roles summary |
| Education Summary | `education_summary` | `{{education_summary}}` | Education background |
| LinkedIn Skills | `linkedin_skills` | `{{linkedin_skills}}` | Listed skills |
| LinkedIn Followers | `followers_count` | `{{followers_count}}` | Follower count |
| Is LinkedIn Premium | `linkedin_premium` | `{{linkedin_premium}}` | Premium account flag |
| Is First Degree Connection | `is_first_degree_connection` | `{{is_first_degree_connection}}` | Connection degree check |
| Person LinkedIn Profile | `person_linkedin` | `{{linkedin}}` | LinkedIn profile URL |

### Company Data

| Column Name | `magic_column_type` | Variable | What It Does |
|-------------|---------------------|----------|--------------|
| Company Name | `company_name` | `{{company_name}}` | Resolved company name |
| Company Website | `company_website` | `{{company_website}}` | Company website URL |
| Company LinkedIn Profile | `company_linkedin` | `{{company_linkedin}}` | Company LinkedIn page URL |
| LinkedIn Company Description | `li_company_description` | `{{linkedin_company_description}}` | Company description from LinkedIn |
| LinkedIn Company Size | `li_company_size` | `{{linkedin_company_size}}` | Size range (e.g., 51-200) |
| LinkedIn Company Country | `li_company_country` | `{{linkedin_company_country}}` | HQ country |
| Company Founded Year | `company_founded_year` | `{{company_founded_year}}` | Year founded |
| Company Employee Count | `li_company_employee_count` | `{{company_employee_count}}` | Employee count |
| Company Website Summary | `website_text_summary` | `{{website_text_summary}}` | AI summary of company website |

### Department Headcounts

| Column Name | `magic_column_type` | Variable |
|-------------|---------------------|----------|
| Sales Headcount | `li_company_people_sales` | `{{linkedin_people_category_sales}}` |
| Engineering Headcount | `li_company_people_engineering` | `{{linkedin_people_category_engineering}}` |
| Marketing Headcount | `li_company_people_marketing` | `{{linkedin_people_category_marketing}}` |
| Research Headcount | `li_company_people_research` | `{{linkedin_people_category_research}}` |
| Operations Headcount | `li_company_people_operations` | `{{linkedin_people_category_operations}}` |
| Human Resources Headcount | `li_company_people_human_resources` | `{{linkedin_people_category_human_resources}}` |
| Business Development Headcount | `li_company_people_business_development` | `{{linkedin_people_category_business_development}}` |

### Email

| Column Name | `magic_column_type` | Variable | What It Does |
|-------------|---------------------|----------|--------------|
| Enrich Emails | `enrich_emails` | `{{email}}` | Finds email addresses for contacts |
| Validate Emails | `validate_emails` | `{{email}}` | Verifies deliverability of found emails |
| Email MX (Host + Provider) | `email_mx` | `{{email_mx_host}}`, `{{email_mx_provider}}` | Resolves MX host from email/website domain and classifies provider |

### AI-Powered Columns (Custom)

These use `magic_column_type: "ai_custom_column"` and require a prompt.
They can reference any variable from columns above. See the `leadspicker-classifier`
skill for detailed prompt-writing instructions and examples.

Common AI enrichments:

| Column Name | Variable | What It Does |
|-------------|----------|--------------|
| Clean First Name | `{{Clean First Name}}` | AI-cleaned first name |
| Clean Company Name | `{{Clean Company Name}}` | AI-cleaned company name |
| Job Title Cleaning | `{{Job Title Cleaning}}` | Standardized job title |
| Company Industry | `{{Company industry}}` | AI-inferred industry |
| B2B/B2C | `{{B2B/B2C}}` | Business model classification |
| Icebreaker - Latest LI Posts | `{{Icebreaker - latest LI posts}}` | Personalized opener from posts |
| LinkedIn Post Summarization | `{{LinkedIn Post Summarization}}` | Summary of recent posts |
| Targeted Job Titles | `{{Targeted Job Titles}}` | Whether title matches target criteria |
| First Name Vocative - CZ | `{{First Name Vocative - CZ}}` | Czech vocative form of first name |
| Last Name Vocative - CZ | `{{Last Name Vocative - CZ}}` | Czech vocative form of last name |

### Other Built-in Types

| Column Name | `magic_column_type` | What It Does |
|-------------|---------------------|--------------|
| HTTP Request | `http_request` | Calls an HTTP endpoint per contact and extracts a value from the JSON response |

---

## Complete `magic_column_type` Quick Reference

Use this table to look up the exact API value for any column:

```
COLUMN NAME                          → magic_column_type
─────────────────────────────────────────────────────────
Company Name                         → company_name
Company Website                      → company_website
Company LinkedIn Profile             → company_linkedin
LinkedIn Company Description         → li_company_description
LinkedIn Company Size                → li_company_size
LinkedIn Company Country             → li_company_country
Company Founded Year                 → company_founded_year
Company Employee Count               → li_company_employee_count
Company Website Summary              → website_text_summary
Person LinkedIn Profile              → person_linkedin
Full Name                            → li_full_name
Position                             → person_position
Person Country                       → person_country
LinkedIn Location                    → li_location
LinkedIn City                        → li_city
LinkedIn About Me                    → li_about_me
LinkedIn Latest Posts                → li_latest_posts
Present Positions Summary            → present_experience
Past Positions Summary               → past_experience
Education Summary                    → education_summary
LinkedIn Skills                      → linkedin_skills
LinkedIn Followers                   → followers_count
Is LinkedIn Premium                  → linkedin_premium
Is First Degree Connection           → is_first_degree_connection
Enrich Emails                        → enrich_emails
Validate Emails                      → validate_emails
Email MX (Host + Provider)           → email_mx
Sales Headcount                      → li_company_people_sales
Engineering Headcount                → li_company_people_engineering
Marketing Headcount                  → li_company_people_marketing
Research Headcount                   → li_company_people_research
Operations Headcount                 → li_company_people_operations
Human Resources Headcount            → li_company_people_human_resources
Business Development Headcount       → li_company_people_business_development
AI Custom Column                     → ai_custom_column
HTTP Request                         → http_request
```

---

## Recommended Pipelines

The order matters — later steps often depend on data from earlier steps. Present these
to the user and let them pick or customize.

### Full Enrichment (for outreach-ready data)

Run in this exact order, waiting for the user to confirm each batch before proceeding:

```
Batch 1 — Core Identity (run all at once):
  → Company Name (company_name)
  → Company Website (company_website)
  → Company LinkedIn Profile (company_linkedin)
  → Person LinkedIn Profile (person_linkedin)
  → Full Name (li_full_name)
  → Position (person_position)

Batch 2 — Company Deep Data (needs Batch 1):
  → LinkedIn Company Description (li_company_description)
  → Company Website Summary (website_text_summary)
  → LinkedIn Company Size (li_company_size)
  → LinkedIn Company Country (li_company_country)
  → Company Founded Year (company_founded_year)
  → Company Employee Count (li_company_employee_count)

Batch 3 — Person Deep Data (needs Batch 1):
  → LinkedIn About Me (li_about_me)
  → Present Positions Summary (present_experience)
  → LinkedIn City (li_city)
  → Person Country (person_country)
  → [OPTIONAL] LinkedIn Latest Posts (li_latest_posts) — only if icebreaker personalization is needed

Batch 4 — Email (needs core identity):
  → Enrich Emails (enrich_emails)
  → Validate Emails (validate_emails) — after email enrichment completes

Batch 5 — AI Columns (needs Batches 1-3 for context):
  → Any classification, scoring, or personalization columns (ai_custom_column)
  → Hand off to leadspicker-classifier skill for prompt crafting
```

### Quick Email Enrichment

```
Step 1: → Enrich Emails (enrich_emails)
Step 2: → Validate Emails (validate_emails)
```

### Company Research

```
Batch 1: → Company Name (company_name), Company Website (company_website),
           Company LinkedIn Profile (company_linkedin)
Batch 2: → LinkedIn Company Description (li_company_description),
           Company Website Summary (website_text_summary),
           LinkedIn Company Size (li_company_size),
           Company Employee Count (li_company_employee_count),
           Company Founded Year (company_founded_year)
Batch 3: → Department headcounts (li_company_people_*) as needed
```

### LinkedIn Person Enrichment

```
Batch 1: → Person LinkedIn Profile (person_linkedin), Full Name (li_full_name),
           Position (person_position)
Batch 2: → LinkedIn About Me (li_about_me), LinkedIn Latest Posts (li_latest_posts),
           Present Positions Summary (present_experience),
           Past Positions Summary (past_experience),
           Education Summary (education_summary), LinkedIn Skills (linkedin_skills)
```

### Outreach Preparation (CZ market)

```
Batch 1-4: → Full Enrichment pipeline above
Batch 5:   → Clean First Name (ai_custom_column)
             → First Name Vocative - CZ (ai_custom_column)
             → Clean Company Name (ai_custom_column)
             → Icebreaker - Latest LI Posts (ai_custom_column)
             → Any classification columns (ai_custom_column)
```

---

## API Calls

### Endpoint

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
```

### Discovering Available Types

You can fetch all available column types (and their categories) via GET:

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns-categories
```

### Headers

```
accept: application/json
content-type: application/json
x-api-key: {api_key}
```

### Body — Built-in Enrichment Column

```json
{
  "magic_column_type": "{type_from_quick_reference}",
  "column_name": "{column_name}"
}
```

### Body — AI Custom Column (with prompt)

```json
{
  "magic_column_type": "ai_custom_column",
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}"
}
```

> In the `prompt` field, escape all newlines as `\n` (JSON string).
> Template variables like `{{company_name}}` are filled by Leadspicker automatically.

### cURL Example — Built-in Column

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "company_website",
    "column_name": "Company Website"
  }'
```

### cURL Example — AI Custom Column

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "ai_custom_column",
    "column_name": "Company Industry",
    "prompt": "Your task is to determine the primary industry of a company.\n\nAnalyze the company data and classify it into one of these industries: SaaS, E-commerce, FinTech, HealthTech, EdTech, Marketing Agency, Consulting, Manufacturing, Retail, Media, Real Estate, Other.\n\nClassify the following company based on the available data:\n\nInput Fields:\n- Company Name: {{company_name}}\n- Company Website: {{company_website}}\n- Company LinkedIn Profile: {{company_linkedin}}\n- LinkedIn Company Description: {{linkedin_company_description}}\n- Company Website Summary: {{website_text_summary}}\n\nRespond in this exact format and nothing else:\n\nclassification: [industry name]\nscore: 1-10\nreasoning: one sentence explaining your decision"
  }'
```

---

## Workflow Step by Step

### Step 1: Collect Input

Gather `project_id`, `api_key`, and the user's enrichment request.

### Step 2: Determine Mode and Build the Plan

**Selective mode** (user named specific columns):
1. Match the user's words to columns in the Available Enrichment Columns tables
2. Look up the `magic_column_type` from the table (this is the value you send to the API)
3. Check the Dependency Map — add any missing prerequisites
4. Group into batches: prerequisites first, then requested columns
5. Present the plan showing what's a prerequisite vs. what they asked for

Example output to show user:
```
I'll enrich these columns for project 26256:

Prerequisites (needed first):
  → Company LinkedIn Profile (company_linkedin)
  → Company Website (company_website)

Your requested columns:
  → LinkedIn Company Description (li_company_description)
  → Company Website Summary (website_text_summary)

Total: 4 API calls in 2 batches. OK to proceed?
```

**Pipeline mode** (user described a goal):
1. Pick the best matching pipeline from Recommended Pipelines
2. Present the full pipeline with all batches

### Step 3: Confirm with User

Before any API call, show the plan and get explicit approval.
For AI columns: show the prompt text (or hand off to `leadspicker-classifier` skill).

### Step 4: Execute

For each batch:
1. Run all columns in the batch (one API call per column)
2. Add a 1-second delay between API calls to avoid rate limiting
3. Report results — which succeeded, which failed
4. Leadspicker processes columns asynchronously — data appears over the next few minutes

For selective mode with only 1-2 batches, you can proceed without waiting between batches
if none of the requested columns depend on the prerequisites being fully populated yet.
For pipeline mode or when later batches genuinely need earlier data, ask the user to confirm
each batch completed in Leadspicker before proceeding.

### Step 5: Report Summary

After all calls complete, report:
- Columns created (distinguishing prerequisites from requested)
- Any failures and how to resolve them
- Suggested next steps based on what was enriched:
  - After company data → "You can now run AI classification on this data"
  - After email enrichment → "Consider validating the emails next"
  - After LinkedIn person data → "Good base for icebreaker or personalization columns"

---

## Natural Language → Column Matching

Users won't always use exact column names. Here's how to map common phrases:

| User says something like... | Maps to column(s) | `magic_column_type` |
|---|---|---|
| "company description", "co popísek firmy", "popis firmy" | LinkedIn Company Description | `li_company_description` |
| "website summary", "shrnutí webu", "co dělá firma" | Company Website Summary | `website_text_summary` |
| "find emails", "najdi emaily", "get email addresses" | Enrich Emails | `enrich_emails` |
| "verify emails", "validuj emaily", "check emails" | Validate Emails | `validate_emails` |
| "LinkedIn data", "LinkedIn info" | All LinkedIn person columns | (multiple) |
| "company info", "firemní data" | All Company Data columns | (multiple) |
| "job title", "pozice", "co dělá" | Position | `person_position` |
| "headcount", "team size", "kolik lidí" | Department Headcount columns | `li_company_people_*` |
| "everything", "full enrichment", "všechno" | Full Enrichment pipeline | (multiple) |
| "prepare for outreach", "připrav na outreach" | Outreach Preparation pipeline | (multiple) |
| "company size", "velikost firmy" | LinkedIn Company Size + Company Employee Count | `li_company_size` + `li_company_employee_count` |
| "posts", "příspěvky", "co publikuje" | LinkedIn Latest Posts | `li_latest_posts` |
| "bio", "about", "o sobě" | LinkedIn About Me | `li_about_me` |
| "skills", "dovednosti" | LinkedIn Skills | `linkedin_skills` |
| "industry", "odvětví" | Company Industry (AI column) | `ai_custom_column` |
| "icebreaker", "opener" | Icebreaker - Latest LI Posts (AI column) | `ai_custom_column` |
| "email host", "email provider", "MX" | Email MX | `email_mx` |

When in doubt, show the user the column list and ask them to pick.

---

## Error Handling

| HTTP Status | Likely Cause | Resolution |
|-------------|-------------|------------|
| `401 Unauthorized` | Bad or expired API key | Verify `x-api-key` with user |
| `404 Not Found` | Wrong `project_id` | Verify project ID |
| `400 Bad Request` | Invalid `magic_column_type` value | Check the Quick Reference table for the correct type |
| `422 Unprocessable` | Column already exists or invalid prompt | Check if column name is unique |
| `429 Too Many Requests` | Rate limit on batch | Increase delay between calls to 2-3s |

---

## Security

- **Never log or display** the full API key — confirm only the last 6 characters
- Use the API key only for Leadspicker API calls, never send it elsewhere
- Before running any batch, **always show the plan to the user** for approval
- For AI columns, **always show the prompt** before calling the API
