---
name: leadspicker-robots
description: >
  Creates and launches Leadspicker robots (automations) that scrape LinkedIn data and deposit leads
  into projects. Supports 4 robot types: scraping likers and commenters from specific LinkedIn posts,
  monitoring new posts by LinkedIn profiles or companies, searching LinkedIn posts by keywords, and
  LinkedIn people search via Sales Navigator URLs, normal LinkedIn people search, or event attendees.
  Use this skill whenever the user wants to create, launch, or start a robot or automation in
  Leadspicker — in any language. Triggers on any request involving scraping LinkedIn posts, extracting
  post likers or commenters, monitoring posts from profiles or companies, searching LinkedIn content
  by keywords or topics, LinkedIn people search, Sales Navigator search, event attendees scraping,
  or when the user pastes LinkedIn URLs and asks to scrape, monitor, or search. Also triggers on
  direct robot type references: li_posts_extract, li_posts_monitor, li_posts_feed, salesnav_monitor.
---

# Leadspicker Robots Orchestrator

Creates and launches robots (LinkedIn scraping automations) in Leadspicker via `POST /robots`.
Each robot scrapes LinkedIn data and deposits the results as leads into a target Leadspicker project.

**4 supported robot types:**

| Robot Type | `robot_type` | What it does |
|---|---|---|
| Post Scrape | `li_posts_extract` | Scrape likers/commenters from specific LinkedIn posts |
| Post Monitor | `li_posts_monitor` | Track new posts by specific LinkedIn profiles or companies |
| Post Feed Search | `li_posts_feed` | Search LinkedIn posts by keywords |
| People Search | `salesnav_monitor` | LinkedIn people search (Sales Navigator, normal search, event attendees) |

---

## User Input

Always collect (or confirm you have) these parameters before making any API calls:

| Parameter | Required | Description | Example |
|---|---|---|---|
| `api_key` | Yes | From `credentials/leadspicker.json`, confirm last 6 chars | `...b4507ee2f` |
| `target_project_id` | Yes | Leadspicker project to deposit leads into | `30877` |
| URL(s) | Yes | One or more LinkedIn URLs — determines robot type | See URL Detection below |

If any parameter is missing, ask for ALL missing ones in a single follow-up — not one by one.

### Target Project Selection (when no project ID is provided)

If the user does not provide a `target_project_id`, fetch their projects and let them choose:

1. Fetch recent projects:
   ```
   GET https://app.leadspicker.com/app/sb/api/projects?order_by_field=last_active&order_direction=desc&limit=20
   ```
   Headers: `accept: application/json`, `x-api-key: {api_key}`

2. Present projects to the user:
   ```
   Which project should receive the scraped leads?

   | # | Project Name | ID | Last Active |
   |---|---|---|---|
   | 1 | CEOs Czechia | 30877 | 2026-03-23 |
   | 2 | SaaS Founders | 30512 | 2026-03-21 |
   | ... | ... | ... | ... |
   | New | Create a new project | — | — |

   Pick a number or say "new" to create one.
   ```

3. If the user picks an existing project → use its `id` as `target_project_id`.

4. If the user wants a new project → ask for a project name, then create it:
   ```
   POST https://app.leadspicker.com/app/sb/api/projects
   ```
   Body:
   ```json
   {
     "name": "{user_provided_name}",
     "timezone": "Europe/Prague"
   }
   ```
   Use the returned `id` as `target_project_id`.

5. If the user provides a search term instead of picking a number (e.g., "the SaaS project"), use the search parameter:
   ```
   GET https://app.leadspicker.com/app/sb/api/projects?search_query={term}&search_in_name=true&limit=5
   ```
   Then present the filtered results.

---

## URL Detection — Auto-Routing to Robot Type

The skill automatically detects which robot type to use based on the URL(s) provided:

| URL Pattern | Robot Type | Example |
|---|---|---|
| Contains `/feed/update/` or `/posts/` | `li_posts_extract` | `https://www.linkedin.com/feed/update/urn:li:activity:7441864955731103744/` |
| Contains `/in/` or `/company/` (profile page, NOT a search URL) | `li_posts_monitor` | `https://www.linkedin.com/in/tblatak/` or `https://www.linkedin.com/company/leadspicker` |
| Contains `/search/results/content` | `li_posts_feed` | `https://www.linkedin.com/search/results/content/?keywords=%22leadspicker%22` |
| Contains `/sales/search/people` | `salesnav_monitor` | Sales Navigator people search URL |
| Contains `/search/results/people` (without `eventAttending`) | `salesnav_monitor` | `https://www.linkedin.com/search/results/people/?keywords=ceo` |
| Contains `eventAttending` | `salesnav_monitor` | `https://www.linkedin.com/search/results/people/?origin=EVENT_PAGE_CANNED_SEARCH&eventAttending=...` |

**Important URL matching rules:**
- Profile URLs (`/in/username` or `/company/name`) that are NOT inside a search URL → `li_posts_monitor`
- If the URL pattern is ambiguous, ask the user which robot type they intend
- Multiple URLs of the same type are fine — they go into `robot_urls` separated by newlines
- Do NOT mix URL types in a single robot — if the user provides mixed URLs, create separate robots

---

## Robot Type Details

### 1. `li_posts_extract` — Scrape Specific Posts

Scrapes likers and commenters from specific LinkedIn post URLs.

**URL input:** One or more LinkedIn post URLs (containing `/feed/update/` or `/posts/`)

| Field | Value | Notes |
|---|---|---|
| `frequency` | `"once"` | Always once — do not ask |
| `max_likers` | `250` | Default — user can override |
| `max_commenters` | `250` | Default — user can override |
| `max_posts` | `500` | Default |
| `should_scrape_authors` | `false` | Always false — do not ask |
| `max_post_age` | — | Not applicable for this type |
| `linkedin_account_id` | — | Not needed — omit from payload |

**What to ask the user (beyond required inputs):** Nothing extra by default. Use defaults and proceed.

---

### 2. `li_posts_monitor` — Track Posts by Account

Monitors posts published by specific LinkedIn profiles or company pages.

**URL input:** One or more LinkedIn profile URLs (`/in/...`) or company URLs (`/company/...`)

| Field | Value | Notes |
|---|---|---|
| `max_post_age` | `"month"` | Default. Options: `"day"`, `"week"`, `"month"`, `"year"`, `"any"` |
| `frequency` | `"once"` | Default. Options: `"once"`, `"daily"`, `"3days"`, `"weekly"` |
| `max_posts` | `500` | Default |
| `max_likers` | `250` | Default |
| `max_commenters` | `250` | Default |
| `should_scrape_authors` | `false` | Always false — do not ask |
| `linkedin_account_id` | — | Optional — omit by default |

**What to ask the user:**
- How far back to look for posts (`max_post_age`) — suggest `"month"` as default
- Whether they want recurring runs (`frequency`) — suggest `"once"` as default
- Only ask about `max_likers`/`max_commenters`/`max_posts` if user indicates custom limits

---

### 3. `li_posts_feed` — Search Posts by Keywords

Searches LinkedIn for posts matching specific keywords.

**URL input:** LinkedIn content search URL (containing `/search/results/content`)

| Field | Value | Notes |
|---|---|---|
| `should_scrape_authors` | `true` | Always true for keyword search — do not ask |
| `max_post_age` | `"week"` | Default. Options: `"day"`, `"week"`, `"month"`, `"year"`, `"any"` |
| `frequency` | `"once"` | Default. Options: `"once"`, `"daily"`, `"3days"`, `"weekly"` |
| `max_posts` | `500` | Default |
| `max_likers` | `250` | Default |
| `max_commenters` | `250` | Default |
| `linkedin_account_id` | — | Optional — omit by default |

**What to ask the user:**
- Same as `li_posts_monitor`: `max_post_age` and `frequency`

---

### 4. `salesnav_monitor` — LinkedIn People Search

Searches for people on LinkedIn via Sales Navigator, normal LinkedIn search, or event attendees.

**If the user needs to build a Sales Navigator search URL from filters (companies, titles, seniority, geography, etc.), use the `sales-nav-url-builder` skill first.** It generates valid Sales Nav URLs programmatically from natural language descriptions. Then use the generated URL as `robot_urls` input here.

**URL input:** One of three types:
- **Sales Navigator search URL** — contains `/sales/search/people`
- **Normal LinkedIn people search URL** — contains `/search/results/people` (no `eventAttending`)
- **Event attendees URL** — contains `eventAttending`

| Field | Value | Notes |
|---|---|---|
| `max_posts` | `500` | **IMPORTANT: Despite the field name, this controls max number of PEOPLE to scrape, not posts. The API reuses this field.** Default 500. |
| `max_likers` | `0` | Not relevant for people search |
| `max_commenters` | `0` | Not relevant for people search |
| `should_scrape_authors` | `true` | Always true |
| `max_post_age` | `"all"` | Default for people search |
| `frequency` | `"once"` | Default. Supports recurring |
| `linkedin_account_id` | **See below** | Required for Sales Nav and event URLs |

#### LinkedIn Account Selection

| URL Type | `linkedin_account_id` | Why |
|---|---|---|
| Sales Navigator URL | **Required** | Needs a LinkedIn account with Sales Navigator access |
| Event Attendees URL | **Required** | Needs a LinkedIn account that has attended the event |
| Normal People Search URL | Optional | Omit by default |

**When `linkedin_account_id` is required, follow this flow:**

1. Fetch available LinkedIn accounts:
   ```
   GET https://app.leadspicker.com/app/sb/api/linkedin-accounts
   ```
   Headers: `accept: application/json`, `x-api-key: {api_key}`

2. Filter accounts:
   - Always filter out: `is_revoked: true`
   - For Sales Navigator URLs: further filter to `sales_nav_session_connected: true`
   - For Event Attendees URLs: further filter to `linkedin_session_connected: true`

3. Present valid accounts to the user:
   ```
   Available LinkedIn accounts:

   | # | Name | ID | Sales Nav | Status |
   |---|------|-----|-----------|--------|
   | 1 | Dalibor Rokyta | 4773 | Yes | Connected |
   | 2 | Anna Hanušová | 4702 | Yes | Connected |
   | ...

   Which account should I use for this search?
   ```

4. Use the selected account's `id` as `linkedin_account_id` in the robot payload.

5. If no valid accounts are found, stop and tell the user:
   - For Sales Nav: "No LinkedIn accounts with Sales Navigator connected. Please connect one in Leadspicker first."
   - For Events: "No connected LinkedIn accounts found. Please connect one in Leadspicker first."

---

## Common Payload Template

All robots use `POST https://app.leadspicker.com/app/sb/api/robots` with this payload structure:

```json
{
  "name": "{auto_generated_name}",
  "robot_type": "{detected_robot_type}",
  "robot_urls": "{newline_separated_urls}",
  "target_project_id": {project_id_integer},
  "frequency": "{frequency}",
  "deduplicate_results": true,
  "status": "ready",
  "max_posts": {max_posts},
  "max_likers": {max_likers},
  "max_commenters": {max_commenters},
  "should_scrape_authors": {true_or_false},
  "prefer_post_contact": true,
  "id": null,
  "last_run": null,
  "lead_count": null,
  "start_time": null,
  "statuses": null,
  "statuses_people": null,
  "target_project_name": null,
  "autocph_positions": "",
  "cron_expression": "",
  "geo_filter": "",
  "person_gpt_prompt": "",
  "post_gpt_prompt": ""
}
```

**Conditionally included fields:**
- `linkedin_account_id: {id}` — only when required/provided (for `salesnav_monitor` with Sales Nav or event URLs)
- `max_post_age: "{value}"` — only for `li_posts_monitor`, `li_posts_feed`, and `salesnav_monitor`

**Auto-generated robot name format:**
```
{Type Label} ({DD. M. YYYY HH:MM:SS})
```

| Robot Type | Type Label |
|---|---|
| `li_posts_extract` | `Post Tracker` |
| `li_posts_monitor` | `Post Tracker` |
| `li_posts_feed` | `Post Tracker` |
| `salesnav_monitor` | `LinkedIn people` |

Example: `Post Tracker (23. 3. 2026 17:45:28)` or `LinkedIn people (23. 3. 2026 18:10:02)`

---

## Workflow Step by Step

### Step 1: Load Credentials

Read `credentials/leadspicker.json` to get the API key. Confirm the last 6 characters with the user.

### Step 2: Collect Input

Gather:
- `target_project_id` — if the user didn't provide one, run the **Target Project Selection** flow (fetch projects, let user pick or create new)
- URL(s) to scrape/monitor/search

### Step 3: Detect Robot Type

Apply the URL Detection rules to determine which `robot_type` to use.
Tell the user which type was detected:
```
Detected: Post Scrape (li_posts_extract) — scraping likers and commenters from 2 LinkedIn posts.
```

### Step 4: Collect Type-Specific Parameters

Based on the detected robot type, ask the user about relevant parameters.
Use defaults for everything else — don't ask about fields with fixed values.

**For `li_posts_extract`:** No additional questions — proceed with defaults.

**For `li_posts_monitor`:**
- Ask about `max_post_age` (default: `"month"`)
- Ask about `frequency` (default: `"once"`)

**For `li_posts_feed`:**
- Ask about `max_post_age` (default: `"week"`)
- Ask about `frequency` (default: `"once"`)

**For `salesnav_monitor`:**
- If Sales Navigator or event URL → execute LinkedIn Account Selection flow (see above)
- Ask about `frequency` if relevant (default: `"once"`)

### Step 5: Build and Show Payload

Assemble the full JSON payload with all values filled in.
Show the payload to the user for approval:

```
Robot payload ready:

Type: Post Scrape (li_posts_extract)
Target project: 30877
URLs: 2 LinkedIn posts
Max likers: 250 | Max commenters: 250
Frequency: once

Full payload:
{...JSON...}

Ready to launch this robot. Proceed?
```

### Step 6: Execute

After user approval:

```
POST https://app.leadspicker.com/app/sb/api/robots
```

Headers:
```
accept: application/json
content-type: application/json
x-api-key: {api_key}
```

Body: the assembled payload from Step 5.

### Step 7: Confirm Result

Report the result to the user:
- Success: show robot ID from response, robot name, type, target project
- If recurring: note the frequency
- Error: show HTTP status and resolution from Error Handling table

---

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/robots` | Create and launch a robot |
| `GET` | `/linkedin-accounts` | List available LinkedIn accounts (for account selection) |
| `GET` | `/projects` | List projects (for target project selection) |
| `POST` | `/projects` | Create a new project |

**Base URL:** `https://app.leadspicker.com/app/sb/api`

**Headers (all calls):**
```
accept: application/json
content-type: application/json
x-api-key: {api_key}
```

### cURL Example — Post Scrape Robot

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/robots" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "name": "Post Tracker (23. 3. 2026 17:45:28)",
    "robot_type": "li_posts_extract",
    "robot_urls": "https://www.linkedin.com/feed/update/urn:li:activity:7441864955731103744/",
    "target_project_id": 30877,
    "frequency": "once",
    "deduplicate_results": true,
    "status": "ready",
    "max_posts": 500,
    "max_likers": 250,
    "max_commenters": 250,
    "should_scrape_authors": false,
    "prefer_post_contact": true,
    "id": null,
    "last_run": null,
    "lead_count": null,
    "start_time": null,
    "statuses": null,
    "statuses_people": null,
    "target_project_name": null,
    "autocph_positions": "",
    "cron_expression": "",
    "geo_filter": "",
    "person_gpt_prompt": "",
    "post_gpt_prompt": ""
  }'
```

### cURL Example — People Search with LinkedIn Account

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/robots" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "name": "LinkedIn people (23. 3. 2026 18:10:02)",
    "robot_type": "salesnav_monitor",
    "robot_urls": "https://www.linkedin.com/sales/search/people?query=...",
    "target_project_id": 30877,
    "linkedin_account_id": 4773,
    "frequency": "once",
    "deduplicate_results": true,
    "status": "ready",
    "max_posts": 500,
    "max_likers": 0,
    "max_commenters": 0,
    "max_post_age": "all",
    "should_scrape_authors": true,
    "prefer_post_contact": true,
    "id": null,
    "last_run": null,
    "lead_count": null,
    "start_time": null,
    "statuses": null,
    "statuses_people": null,
    "target_project_name": null,
    "autocph_positions": "",
    "cron_expression": "",
    "geo_filter": "",
    "person_gpt_prompt": "",
    "post_gpt_prompt": ""
  }'
```

---

## Error Handling

| HTTP Status | Likely Cause | Resolution |
|---|---|---|
| `401 Unauthorized` | Bad or expired API key | Verify `x-api-key` with user (last 6 chars) |
| `404 Not Found` | Wrong `target_project_id` or endpoint | Confirm project ID with user |
| `400 Bad Request` | Invalid JSON, missing required field, or bad URL format | Check payload structure and URL validity |
| `422 Unprocessable` | Invalid `robot_type` or other validation error | Verify robot_type matches one of the 4 supported types |
| `429 Too Many Requests` | Rate limit | Wait 2-3 seconds and retry |

---

## Security

- **Never log or display** the full API key — confirm only the last 6 characters
- Use the API key only for Leadspicker API calls, never send it elsewhere
- Before launching any robot, **always show the full payload** to the user for approval
- Never execute without explicit user confirmation
