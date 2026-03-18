---
name: leadspicker-classifier
description: >
  Creates AI-powered classification and data processing columns in Leadspicker.com projects
  Use this skill whenever the user wants to classify, score, label, tag,
  clean, or transform contact/company data in Leadspicker — for example "classify companies
  as SaaS", "is this person a decision maker", "determine company industry", "clean job titles",
  "create an icebreaker from LinkedIn posts", "is the company B2B or B2C", "classify leads
  as relevant", "chci klasifikovat firmy", "urči odvětví", "vyčisti název firmy",
  "je ten člověk relevantní", or any request to add an AI-powered magic column to a
  Leadspicker project. Also triggers when the user mentions AI classification, lead scoring,
  contact tagging, data cleaning, or personalization columns in the context of Leadspicker.
---

# Leadspicker AI Classifier

Creates AI-powered magic columns in Leadspicker projects via the magic-columns API.
Each column runs gpt-realtime on every contact in the project to classify, categorize,
clean, or generate personalized content.

This skill is a companion to `leadspicker-data-enrichment` — it uses the enriched data
(company descriptions, website summaries, job titles, LinkedIn profiles) as input for
AI classification prompts.

---

## User Input

Always collect (or confirm you have) these parameters before making any API calls:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `project_id` | Leadspicker project ID | `29841` |
| `api_key` | User's API key (`x-api-key`) | `fd1f0d98...` |
| Classification request | What the user wants to classify or generate | `"Is this a SaaS company?"` or `"Determine company industry"` |
| `column_name` | Name for the new column | `"Is SaaS"` or `"Company Industry"` |

If the user doesn't provide a `column_name`, generate a clear, short one from the
classification goal (e.g., "Is SaaS Company", "Industry", "Relevant Decision Maker").

---

## System Prompt (Fixed — Do Not Modify)

Every AI column in Leadspicker is wrapped by a fixed system prompt that you **cannot change**.
The system prompt forces gpt-realtime to output strict JSON. Understanding this is critical
for writing effective user prompts.

**Boolean mode** (`is_boolean: true`):
```
System forces output: {"result": true | false, "message": "A short explanation."}
```

**String mode** (`is_boolean: false`):
```
System forces output: {"result": "response"}
```

**What this means for your prompts:**
- NEVER ask gpt-realtime to output `yes/no`, `classification: yes/no`, or any custom format
- NEVER include output format instructions — the system prompt handles that
- Just describe the task, the criteria, and provide the input variables
- The system prompt will force the correct JSON structure automatically
- For boolean: gpt-realtime returns `yes`/`no` with a message
- For string: gpt-realtime returns a text value in the `result` field

---

## Output Mode Decision

Decide automatically based on what the user is asking:

**Use `is_boolean: true` when the answer is a simple yes/no:**
- "Is this a SaaS company?" → boolean
- "Is this person a decision maker?" → boolean
- "Is this company B2B?" → boolean
- "Is this lead relevant for our outreach?" → boolean
- "Does this company target enterprise?" → boolean

Best for quick filtering where you just need a true/false flag without additional context.

**Use `is_boolean: false` (string) when the answer is a value, label, or text:**
- "What industry is this company in?" → string
- "Clean the job title" → string
- "Write an icebreaker from LinkedIn posts" → string
- "Clean the first name" → string
- "Classify as B2B or B2C" → string (two categories, not yes/no)
- "Summarize the LinkedIn post" → string
- "What department does this person belong to?" → string

**Use `is_boolean: false` (string) with scored classification for complex decisions:**

For more nuanced classification where simple yes/no is not enough, use string mode with
a structured format that combines classification + confidence score + reasoning in one column.

Format: `"Yes | score | reasoning"` or `"No | score | reasoning"`

- "Is this a sales tech company? Include confidence and reasoning" → string scored
- "Is this person relevant for outreach? Score your confidence" → string scored
- Any classification where the user needs to understand WHY and HOW CONFIDENT the AI is

This is especially useful when:
- The classification criteria are complex or ambiguous
- The user wants to filter by confidence level (e.g., only act on score >= 7)
- The user needs to review and understand the AI's reasoning
- The dataset has mixed/borderline cases where a simple yes/no loses context

**Rule of thumb:** Simple filtering → boolean. Multiple categories or free-text → string.
Complex yes/no decisions where confidence and reasoning matter → string with score.

---

## Smart Variable Selection

Pick only the variables relevant to the classification. Do not dump all variables into
every prompt — keep it lean so gpt-realtime focuses on what matters.

### Company Classification

When classifying or categorizing **companies** (industry, B2B/B2C, SaaS, agency, etc.):

```
Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Person Classification — Basic

When checking **job title relevance** (is this person a CEO, decision maker, etc.):

```
Input:
- Position: {{position}}
```

### Person Classification — Detailed

When you need **deeper person analysis** (experience, background, skills):

```
Input:
- Position: {{position}}
- LinkedIn About Me: {{linkedin_about_me}}
- Present Positions Summary: {{present_experiences}}
- Past Positions Summary: {{past_experiences}}
```

### Mixed (Person + Company)

When classification depends on both (e.g., "Is this person a relevant lead at a SaaS company?"):

```
Input:
- Position: {{position}}
- Company Name: {{company_name}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### How to Decide

| User asks about... | Variable set | Example |
|---|---|---|
| Company type, industry, business model | Company | "Is this a SaaS company?" |
| Job title match, role relevance | Person Basic | "Is this a C-level executive?" |
| Person background, experience fit | Person Detailed | "Has this person worked in sales leadership?" |
| Lead relevance (person + company fit) | Mixed | "Is this a relevant lead for our SaaS product?" |
| Name cleaning | Single variable | "Clean first name" → `{{full_name}}`, `{{linkedin}}` |
| Job title cleaning | Single variable | "Clean job title" → `{{position}}` |
| Company name cleaning | Single variable | "Clean company name" → `{{company_name}}` |
| Icebreaker from posts | Single variable | "Write icebreaker" → `{{linkedin_latest_posts}}` |
| Post summarization | Single variable | "Summarize posts" → `{{linkedin_latest_posts}}` |

---

## Prompt Writing Guidelines for gpt-realtime

### Structure

Every prompt should follow this pattern:

```
1. Task definition — one clear sentence stating what to do
2. Criteria / Rules — specific conditions, definitions, examples
3. Input variables — the Leadspicker template variables
```

### Best Practices

- **Be direct and specific.** gpt-realtime performs best with clear, unambiguous instructions.
  Bad: "Try to figure out what kind of company this is."
  Good: "Determine the primary industry of the company."

- **Define boundaries clearly.** For boolean classifications, always state what IS and what
  IS NOT the target category.
  Example: "A SaaS company sells software via cloud on subscription. Do NOT classify as SaaS:
  agencies, consultancies, e-commerce, hardware companies."

- **Keep prompts concise.** gpt-realtime works well with shorter prompts. Avoid unnecessary
  preamble or over-explanation. Aim for 50-150 words.

- **Use simple language.** Avoid complex sentence structures. Short sentences, clear logic.

- **List acceptable values for string mode.** When classifying into categories, explicitly
  list all valid outputs.
  Example: "Classify into exactly one of: SaaS, E-commerce, Agency, Consulting, Manufacturing, Other."

- **Handle missing data.** Always include a fallback instruction.
  For boolean: "If there is not enough data to decide, answer no."
  For string: "If there is not enough data, return empty string."

- **One task per prompt.** Each AI column does one thing. Don't combine classification + cleaning
  in a single prompt.

### Do NOT

- Do NOT include output format instructions (the system prompt handles JSON formatting)
- Do NOT ask for `classification: yes/no` or `score: 1-10` — this conflicts with the system prompt
- Do NOT write multi-step instructions with numbered output fields
- Do NOT include JSON examples in the prompt — the system prompt already enforces JSON
- Do NOT use the phrase "Respond in this exact format" — format is controlled by the system
- Do NOT write prompts in Czech — always write in English (gpt-realtime performs best in English)

---

## Prompt Examples

### Company: Is SaaS? (boolean)

**Column name:** `Is SaaS`
**`is_boolean`: true**

```
Determine whether this company is a SaaS (Software as a Service) company.

A SaaS company primarily sells software delivered via the cloud on a subscription or recurring basis. This includes B2B SaaS platforms, productivity tools, CRMs, ERPs, developer tools, analytics platforms, and similar products where the core offering is cloud-hosted software.

Do NOT classify as SaaS: marketing agencies, consultancies, IT service providers, e-commerce stores, hardware companies, marketplaces (unless their core product is a software platform), or companies that simply use SaaS tools but sell something else.

If there is not enough information to determine, answer no.

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Company: Industry (string)

**Column name:** `Industry`
**`is_boolean`: false**

```
Determine the primary industry of this company.

Classify into exactly one of these industries: SaaS, E-commerce, FinTech, HealthTech, EdTech, Marketing Agency, Consulting, Manufacturing, Retail, Media, Real Estate, Logistics, Cybersecurity, HR Tech, Legal Tech, Other.

Return only the industry name, nothing else. Use the exact spelling from the list above. If there is not enough data to determine the industry, return "Other".

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Company: B2B or B2C (string)

**Column name:** `B2B/B2C`
**`is_boolean`: false**

```
Determine whether this company primarily operates as B2B (sells to other businesses) or B2C (sells to consumers).

Return exactly one of: "B2B", "B2C", or "Both". If there is not enough data, return "B2B".

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Company: Targets Enterprise? (boolean)

**Column name:** `Targets Enterprise`
**`is_boolean`: true**

```
Determine whether this company primarily targets enterprise customers (large organizations with 500+ employees).

Evidence of enterprise focus includes: enterprise pricing tiers, mentions of Fortune 500 or Global 2000 clients, SOC2/ISO/GDPR compliance certifications, dedicated enterprise sales teams, SSO/SAML support, custom contracts, or case studies featuring large corporations.

Do NOT classify as enterprise-focused if the company only serves SMBs, startups, or individual consumers, even if they mention one or two large clients.

If there is not enough information to determine, answer no.

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Company: Is Sales Tech? — Scored with Reasoning (string)

**Column name:** `Is Sales Tech`
**`is_boolean`: false**

Use this pattern whenever you need yes/no + confidence score + reasoning in one column.

```
Determine whether this company operates in the sales technology (Sales Tech) space, rate your confidence on a scale of 1-10, and provide a one-sentence reasoning.

A Sales Tech company builds or sells technology products that help sales teams sell more effectively. This includes: CRM platforms, sales engagement tools, outreach automation, lead generation software, sales intelligence, pipeline management, revenue operations tools, conversation intelligence, sales enablement platforms, CPQ (configure-price-quote) software, and prospecting tools.

Do NOT classify as Sales Tech: companies that simply use sales tools internally, marketing-only platforms (unless they directly serve sales teams), general business consulting, recruitment platforms, or e-commerce stores.

Return your answer in this exact format: "Yes | score | reasoning" or "No | score | reasoning" where score is a number from 1 (very uncertain) to 10 (absolutely certain), and reasoning is one sentence explaining your decision.

Examples: "Yes | 9 | Company builds a sales engagement platform for outreach automation.", "No | 7 | Company is a marketing agency that does not build sales technology."

If there is not enough information, return "No | 1 | Not enough data to determine."

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

**Scored classification prompt template (reusable pattern):**

When the user wants any scored classification, follow this structure:

```
Determine whether [CLASSIFICATION_GOAL], rate your confidence on a scale of 1-10, and provide a one-sentence reasoning.

[DETAILED_CRITERIA — what IS and what IS NOT the target category]

Return your answer in this exact format: "Yes | score | reasoning" or "No | score | reasoning" where score is a number from 1 (very uncertain) to 10 (absolutely certain), and reasoning is one sentence explaining your decision.

Examples: "Yes | 9 | [example reasoning]", "No | 7 | [example reasoning]"

If there is not enough information, return "No | 1 | Not enough data to determine."

Input:
[relevant variables]
```

### Scored → Boolean Derived Column (reusable pattern)

When a scored classification exists (e.g., "Company Relevance" or "Position Relevance"),
create a follow-up boolean column that reads the scored result and converts it to true/false
based on a threshold.

**Column name:** `Is {Category}` (e.g., `Is Relevant Company`, `Is Relevant Position`)
**`is_boolean`: true**
**Requires:** The scored column must be fully processed before launching this column.

```
You are given the result of a previous classification. The result is in the format
"Yes | score | reasoning" or "No | score | reasoning".

Answer yes ONLY if the answer starts with "Yes" AND the score is 7 or higher.
Answer no in all other cases (answer is "No", score is below 7, or data is missing/empty).

Input:
- {Scored Column Name}: {{{scored_column_variable}}}
```

**Example for company relevance:**
- Input variable: `{{company_relevance}}`
- Column name: `Is Relevant Company`

**Example for position relevance:**
- Input variable: `{{position_relevance}}`
- Column name: `Is Relevant Position`

**The threshold (7) can be adjusted per user request** — some users want >= 5 (broader),
others want >= 9 (stricter). Default to 7 unless specified.

---

### Person: Relevant Decision Maker (boolean)

**Column name:** `Is Decision Maker`
**`is_boolean`: true**

```
Determine whether this person holds a decision-making position.

A decision maker is someone with authority to approve purchases or strategic initiatives. This includes: CEO, CTO, COO, CFO, CMO, VP, Director, Head of Department, Partner, Founder, Co-Founder, Owner, General Manager, Managing Director.

Do NOT classify as decision maker: individual contributors, specialists, analysts, coordinators, assistants, interns, or junior roles even if they have inflated titles.

If there is not enough information to determine, answer no.

Input:
- Position: {{position}}
```

### Person: Relevant for Outreach — Detailed (boolean)

**Column name:** `Is Relevant Lead`
**`is_boolean`: true**

This example shows how to use the detailed person variable set when the user provides
specific targeting criteria. The agent should customize the criteria section based on
what the user describes.

```
Determine whether this person is a relevant lead for outreach selling a B2B sales automation tool.

A relevant lead meets ALL of these criteria:
1. Works in sales, business development, revenue operations, or growth
2. Holds a manager-level position or above (Manager, Director, VP, Head of, C-level)
3. Has experience with sales teams or pipeline management

A person is NOT relevant if they: work in unrelated departments (engineering, design, HR), hold junior or individual contributor roles, or work in a completely different field.

If there is not enough information to determine, answer no.

Input:
- Position: {{position}}
- LinkedIn About Me: {{linkedin_about_me}}
- Present Positions Summary: {{present_experiences}}
- Past Positions Summary: {{past_experiences}}
```

### Data Cleaning: Clean First Name (string)

**Column name:** `Clean First Name`
**`is_boolean`: false**

```
Extract and clean the first name from the input for use in cold email campaigns.

Rules:
- Extract only the first name (e.g., "Ing. Vlastimil Vodicka" → "Vlastimil")
- Remove all titles, degrees, emojis, special characters, and extra spaces
- Return the name in title case (first letter uppercase, rest lowercase)
- If the full name is missing or unrecognizable, try to extract the first name from the LinkedIn URL handle (e.g., linkedin.com/in/trinahymes → "Trina")
- If no name can be determined, return empty string

Input:
- Full Name: {{full_name}}
- LinkedIn: {{linkedin}}
```

### Data Cleaning: Clean Company Name (string)

**Column name:** `Clean Company Name`
**`is_boolean`: false**

```
Clean the company name for use in cold email campaigns.

Remove all legal suffixes and unnecessary additions: LTD, LLC, Limited, GmbH, s.r.o., a.s., Inc, Corp, Corporation, Limited Liability Company, and similar. Also remove special characters, bullet points, taglines, and slogans that are appended to the name.

Return the clean company name in title case. If the name is already clean, return it as-is.

Examples: "Promoly LTD" → "Promoly", "GOOGLE LLC" → "Google", "Fitune • Fitness & Wellness Software" → "Fitune"

Input:
- Company Name: {{company_name}}
```

### Data Cleaning: Clean Job Title (string)

**Column name:** `Clean Job Title`
**`is_boolean`: false**

```
Clean the job title by removing unnecessary additions that people often include.

Remove: hiring announcements ("We're Hiring", "Hiring!"), personal branding slogans, emojis, hashtags, pipe separators with promotional text, and any text after "at" or "@" (company names).

Keep the core job title and its responsibility level intact. Make it concise without changing the seniority or function.

Example: "CEO || We're Hiring" → "CEO", "Senior Dev 🚀 | Building the future" → "Senior Dev"

Input:
- Position: {{position}}
```

### Personalization: Icebreaker from LinkedIn Posts (string)

**Column name:** `Icebreaker`
**`is_boolean`: false**

```
Write a personalized icebreaker sentence for a cold email based on the person's latest LinkedIn post.

Rules:
- Start with "I noticed"
- If the input is a personal post, use "I noticed on your LinkedIn..."
- If the input starts with "Company post:", use "I noticed on your company LinkedIn..."
- Focus on business-related content (product launches, insights, industry opinions). Skip personal posts about vacations, birthdays, etc.
- Keep the output under 15 words
- The icebreaker should feel natural and not salesy

Consider that this sentence will be followed by: "...and thought it might be valuable to connect" — so your output is only the first part starting with "I noticed".

If the input is empty or has no meaningful content, return empty string.

Input:
- LinkedIn Latest Posts: {{linkedin_latest_posts}}
```

### Personalization: Czech First Name Vocative (string)

**Column name:** `First Name Vocative - CZ`
**`is_boolean`: false**

```
You are an expert in Czech grammar, specifically declension rules for the vocative case (5. pad).

Given a Czech first name:
1. Add any missing diacritics (hacky and carky)
2. Transform the name into the correct vocative form

Rules:
- Use only the standard (official) vocative form, never diminutives or familiar forms
- "Marie" → "Marie" (NOT "Marusko")
- "Simona" → "Simono" (NOT "Simonko")
- "Jan" → "Jane"
- "Lukas" → "Lukasi"
- "Michal" → "Michale"
- "Katerina" → "Katerino"
- "Ondrej" → "Ondreji"

Return only the vocative form, nothing else. If no name is provided, return empty string.

Input:
- First Name: {{first_name}}
```

---

## API Calls

### Headers (used for all calls)

```
accept: application/json
content-type: application/json
x-api-key: {api_key}
```

### Preview — Submit Prompt for Testing

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/
```

```json
{
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": true | false
}
```

### Preview — Fetch Results

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/?column_name={column_name}&is_boolean={true|false}
```

Returns: `[{"person": "Name", "result": "value"}, ...]`

### Fetch Contact Data (for preview context)

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/people?page=1&page_size=5
```

Returns: `{"items": [...], "count": N}` where each item has `contact_data` with
`full_name`, `position`, `linkedin`, `company_linkedin`, `company_website`, `company_name`, etc.

### Launch Full Classification

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
```

```json
{
  "magic_column_type": "ai_custom_column",
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": true | false
}
```

> In the `prompt` field, escape all newlines as `\n` (JSON string).
> Template variables like `{{company_name}}` are filled by Leadspicker automatically.
> Set `is_boolean` based on the Output Mode Decision section above.

### cURL Example — Boolean Classification

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "ai_custom_column",
    "column_name": "Is SaaS",
    "prompt": "Determine whether this company is a SaaS (Software as a Service) company.\n\nA SaaS company primarily sells software delivered via the cloud on a subscription or recurring basis. This includes B2B SaaS platforms, productivity tools, CRMs, ERPs, developer tools, analytics platforms, and similar products where the core offering is cloud-hosted software.\n\nDo NOT classify as SaaS: marketing agencies, consultancies, IT service providers, e-commerce stores, hardware companies, marketplaces (unless their core product is a software platform), or companies that simply use SaaS tools but sell something else.\n\nIf there is not enough information to determine, answer no.\n\nInput:\n- Company Name: {{company_name}}\n- Company Website: {{company_website}}\n- LinkedIn Company Description: {{linkedin_company_description}}\n- Company Website Summary: {{website_text_summary}}",
    "is_boolean": true
  }'
```

### cURL Example — String Classification

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "ai_custom_column",
    "column_name": "Industry",
    "prompt": "Determine the primary industry of this company.\n\nClassify into exactly one of these industries: SaaS, E-commerce, FinTech, HealthTech, EdTech, Marketing Agency, Consulting, Manufacturing, Retail, Media, Real Estate, Logistics, Cybersecurity, HR Tech, Legal Tech, Other.\n\nReturn only the industry name, nothing else. Use the exact spelling from the list above. If there is not enough data to determine the industry, return \"Other\".\n\nInput:\n- Company Name: {{company_name}}\n- Company Website: {{company_website}}\n- LinkedIn Company Description: {{linkedin_company_description}}\n- Company Website Summary: {{website_text_summary}}",
    "is_boolean": false
  }'
```

---

## Workflow Step by Step

### Step 1: Collect Input

Gather `project_id`, `api_key`, and the user's classification request.
If the user doesn't provide a `column_name`, generate one from the classification goal.

### Step 2: Determine Classification Type

Based on the user's request, decide:

1. **What is being classified?** → Company, Person, or Mixed
2. **What output mode?** → Boolean (`is_boolean: true`) or String (`is_boolean: false`)
3. **Which variables?** → Select from the Smart Variable Selection tables above

### Step 3: Write the Prompt

Build the prompt following the Prompt Writing Guidelines:
1. Clear task definition
2. Specific criteria with IS / IS NOT boundaries
3. Fallback instruction for missing data
4. Input variables (only the relevant ones)

Remember: do NOT include output format instructions — the system prompt handles that.

### Step 4: Show Prompt to User

Before calling the API, always show the user:
- The column name
- The `is_boolean` setting
- The full prompt text

Ask for approval before proceeding.

### Step 5: Preview — Test on First 5 Rows

**Always run a preview before launching the full classification.** This lets the user
verify the prompt works correctly before applying it to all contacts.

#### 5a. Submit the preview request

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/
```

Body (same schema as `AIPromptPreviewIn`):
```json
{
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": true | false
}
```

#### 5b. Fetch contact data for context

While the preview processes, fetch the first 5 contacts from the project to display
alongside the results:

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/people?page=1&page_size=5
```

The response contains `items[]` where each item has `contact_data` with fields like:
- `contact_data.full_name.value` — Person's name
- `contact_data.position.value` — Job title
- `contact_data.linkedin.value` — Person's LinkedIn URL
- `contact_data.company_linkedin.value` — Company LinkedIn URL
- `contact_data.company_website.value` — Company website URL
- `contact_data.company_name.value` — Company name

#### 5c. Fetch preview results

Wait a few seconds for processing, then fetch the results:

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/?column_name={column_name}&is_boolean={true|false}
```

Returns an array of results:
```json
[
  {"person": "John Doe", "result": "SaaS"},
  {"person": "Jane Smith", "result": "E-commerce"},
  ...
]
```

For boolean mode, the `result` field contains the JSON string with `result` and `message`.

#### 5d. Present combined preview to user

Show a table combining contact data with classification results:

```
Preview Results (first 5 rows):

| Name | Position | Company | Company Website | Person LinkedIn | Result |
|------|----------|---------|-----------------|-----------------|--------|
| John Doe | CEO | Acme Inc | acme.com | linkedin.com/in/john | SaaS |
| Jane Smith | CTO | Shop Co | shop.co | linkedin.com/in/jane | E-commerce |
...

Does this look correct? Should I launch the full classification for all contacts?
```

#### 5e. Wait for user approval

- If the user approves → proceed to Step 6 (full launch)
- If the user wants changes → go back to Step 3, adjust the prompt, and re-run preview
- If the user wants to cancel → stop

### Step 6: Launch Full Classification

Only after the user approves the preview results, execute the full API call:

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
```

```json
{
  "magic_column_type": "ai_custom_column",
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": true | false
}
```

Report the result — success (HTTP 201) or failure with error details.

### Step 7: Report and Suggest Next Steps

After successful creation:
- Confirm the column was created and is now processing all contacts
- Note that Leadspicker processes it asynchronously (data appears in minutes)
- Suggest related classifications if applicable:
  - After industry → "Want to also classify B2B vs B2C?"
  - After SaaS check → "Want to check if they target enterprise?"
  - After decision maker → "Want to create a personalized icebreaker?"

---

## Batch Mode

When the user wants multiple classifications at once:

1. List all requested columns with their names, boolean flags, and prompts
2. Show all prompts to the user for approval in one overview
3. After approval, execute API calls sequentially with 1-second delay between calls
4. Report summary: how many succeeded, how many failed, column names created

---

## Natural Language → Classification Matching

Users won't always use technical terms. Here's how to interpret common requests:

| User says... | Classification type | `is_boolean` | Variable set |
|---|---|---|---|
| "Is this a SaaS company?" | Company boolean | `true` | Company |
| "Is this sales tech? with score and reasoning" | Company scored string | `false` | Company |
| "Classify with confidence level" | Scored string | `false` | Depends on context |
| "What industry?" | Company string | `false` | Company |
| "B2B or B2C?" | Company string | `false` | Company |
| "Is this an agency?" | Company boolean | `true` | Company |
| "Does it target enterprise?" | Company boolean | `true` | Company |
| "Is this person relevant?" | Person boolean | `true` | Person Basic or Detailed |
| "Is this a decision maker?" | Person boolean | `true` | Person Basic |
| "Clean the job title" | Data cleaning string | `false` | `{{position}}` |
| "Clean the first name" | Data cleaning string | `false` | `{{full_name}}`, `{{linkedin}}` |
| "Clean company name" | Data cleaning string | `false` | `{{company_name}}` |
| "Write an icebreaker" | Personalization string | `false` | `{{linkedin_latest_posts}}` |
| "Summarize LinkedIn post" | Personalization string | `false` | `{{linkedin_latest_posts}}` |
| "Czech vocative first name" | Localization string | `false` | `{{first_name}}` |
| "Czech vocative last name" | Localization string | `false` | `{{last_name}}`, `{{first_name}}` |

---

## Error Handling

| HTTP Status | Likely Cause | Resolution |
|-------------|-------------|------------|
| `401 Unauthorized` | Bad or expired API key | Verify `x-api-key` with user |
| `404 Not Found` | Wrong `project_id` | Verify project ID |
| `400 Bad Request` | Malformed body or invalid type | Check JSON formatting and `magic_column_type` spelling |
| `422 Unprocessable` | Column name already exists | Use a different column name |
| `429 Too Many Requests` | Rate limit on batch | Increase delay between calls to 2-3s |

---

## Security

- **Never log or display** the full API key — confirm only the last 6 characters
- Use the API key only for Leadspicker API calls, never send it elsewhere
- Before calling the API, **always show the prompt to the user** for approval
- Write all prompts in English for best gpt-realtime performance
