---
name: leadspicker-ab-testing
description: >
  Splits contacts from a Leadspicker project into multiple equal random batches for A/B testing.
  Use this skill whenever the user wants to split, divide, or distribute contacts across multiple
  projects for testing purposes — for example "A/B test my leads", "split contacts into two
  projects", "divide my project into 3 groups", "copy half the contacts to another project",
  "create test groups from my list", "AB test", "split do projektů", "rozděl kontakty",
  "rozděl projekt na části". Also triggers when the user mentions splitting or distributing
  contacts across Leadspicker projects for any experimental or campaign comparison purpose.
---

# Leadspicker A/B Testing

Splits all contacts from a source project into N equal random batches and distributes them
across N target projects — one batch per project. Use this for A/B (or A/B/C/…) testing
of outreach sequences, messaging variants, or campaign strategies.

This skill supports two modes:

1. **Auto-create mode** — Target projects don't exist yet. The skill creates them automatically
   using the naming convention `{source_project_name}_version_a`, `_version_b`, etc., then
   deletes the original source project (all data has been redistributed).

2. **Existing projects mode** — The user already has target projects. The skill copies N−1
   batches to the provided project IDs. The source project keeps the Nth batch (with copied
   contacts deleted from it), becoming one of the test groups itself.

---

## User Input

Always collect (or confirm you have) these parameters before making any API calls:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `source_project_id` | Leadspicker project to split | `29953` |
| `api_key` | User's Leadspicker API key | `fd1f0d98...` (confirm last 6 chars) |
| `num_splits` | How many equal groups to create | `2`, `3`, `4` |
| `projects_exist` | Are the target projects already created? | `yes` / `no` |

**If `projects_exist = yes`:**
- Collect `num_splits − 1` target project IDs (the source project becomes the final group)
- Example for a 3-way split: collect 2 target project IDs; source project = group C

**If `projects_exist = no`:**
- Ask for `timezone` to use for the new projects (or inherit from the source project — fetch via `GET /projects/{source_project_id}` → `timezone` field)
- Skill creates `num_splits` new projects with versioned names

---

## Mode A: Auto-Create Projects

### Step 1 — Fetch source project details

```
GET https://app.leadspicker.com/app/sb/api/projects/{source_project_id}
```

Extract: `name` (for naming convention) and `timezone` (default for new projects).

### Step 2 — Create target projects

For each split (a, b, c, …):

```
POST https://app.leadspicker.com/app/sb/api/projects
Content-Type: application/json
x-api-key: {api_key}

{
  "name": "{source_name}_version_a",
  "timezone": "{timezone}"
}
```

Repeat for each version. Record the returned project `id` for each.

Letter sequence: a, b, c, d, e, f, … (up to 26 splits, practically 2–4).

### Step 3 — Split and copy

See **Split Logic** and **Copy Execution** sections below.

### Step 4 — Delete original project

After all batches are verified:

```
DELETE https://app.leadspicker.com/app/sb/api/projects/{source_project_id}
```

All data has been redistributed. The source project is no longer needed.

---

## Mode B: Existing Projects

### Step 1 — Validate target project IDs

For each provided project ID, verify it exists:

```
GET https://app.leadspicker.com/app/sb/api/projects/{target_project_id}
```

Confirm the name so the user can verify they gave the right IDs.

### Step 2 — Split and copy

See **Split Logic** and **Copy Execution** sections below.
Copy N−1 batches to the N−1 provided project IDs. The source project keeps the final batch.

### Step 3 — Clean up source project

Delete the contacts that were copied out from the source project:

```
POST https://app.leadspicker.com/app/sb/api/projects/{source_project_id}/persons/mass-delete/
Content-Type: application/json
x-api-key: {api_key}

{
  "selected_ids": [{list of all copied contact IDs}],
  "unselected_ids": [{remaining contact IDs that stay}],
  "all_selected": false
}
```

Result: source project keeps exactly 1 batch; each target project has exactly 1 batch.

---

## Split Logic

### Fetch all contacts (paginated)

```
GET https://app.leadspicker.com/app/sb/api/projects/{source_project_id}/people
  ?page=1&page_size=100
```

Repeat incrementing `page` until `len(items) < page_size` or `total_fetched >= count`.
Collect all `id` values.

### Divide into batches

```
total = len(all_ids)
base  = total // num_splits
remainder = total % num_splits

# Shuffle randomly (no fixed seed)
random.shuffle(all_ids)

batches = []
cursor = 0
for i in range(num_splits):
    size = base + (1 if i < remainder else 0)
    batches.append(all_ids[cursor:cursor + size])
    cursor += size
```

Remainder contacts (when total doesn't divide evenly) go one-each into the first batches.
Example: 335 contacts, 3 splits → batches of 112, 112, 111.

### Show the plan before executing

Present this to the user and get explicit approval:

```
Source project: {source_name} (ID: {source_id}) — {total} contacts

Split plan:
  Group A → {target_name_a} (ID: {id_a}) — {size_a} contacts
  Group B → {target_name_b} (ID: {id_b}) — {size_b} contacts
  ...

After copy:
  [Auto-create mode]  Original project ({source_id}) will be DELETED
  [Existing projects] {size_n} contacts will be DELETED from source project
                      (source project keeps group {last_letter} with {size_n} contacts)

Proceed? (yes/no)
```

---

## Copy Execution

For each batch (except the last batch in Existing Projects mode, which stays in source):

```
POST https://app.leadspicker.com/app/sb/api/projects/{source_project_id}/copy-contacts
Content-Type: application/json
x-api-key: {api_key}

{
  "target_project_id": {target_id},
  "selected_ids": [{batch_ids}],
  "unselected_ids": [{all_other_ids}],
  "all_selected": false,
  "copy_contacts_with_columns": true
}
```

**Important:** `unselected_ids` is required — the API returns 422 if it is missing.
`unselected_ids` = all contact IDs NOT in this batch.

After each copy, verify the target project count before moving to the next batch:

```
GET https://app.leadspicker.com/app/sb/api/projects/{target_id}/people?page=1&page_size=1
```

The copy is **asynchronous** — poll with a 3–5 second delay and retry up to 5 times until `count` matches the expected batch size. If it never matches, stop and alert the user before proceeding to the next batch or deleting the source project.

**Critical:** Never delete the source project until ALL batch copies have been individually verified.

---

## Workflow Step by Step

### Step 1: Collect Input

Ask for `source_project_id`, `api_key` (confirm last 6 chars), `num_splits`, and whether target projects already exist.

### Step 2: Fetch Source Project

- `GET /projects/{source_project_id}` — get name, timezone, confirm it's the right project
- `GET /projects/{source_project_id}/people?page=1&page_size=1` — get total contact count

### Step 3: Set Up Target Projects

**Auto-create:** Create all `num_splits` projects via `POST /projects`. Record their IDs.
**Existing:** Collect `num_splits − 1` project IDs, validate each via `GET /projects/{id}`.

### Step 4: Calculate Split and Show Plan

Shuffle contacts, divide into batches, show the full plan (names, IDs, counts, cleanup action).

### Step 5: Get User Approval

Do not execute anything until the user explicitly confirms.

### Step 6: Copy All Batches

Copy each batch sequentially. For each:
1. POST the copy request
2. Poll the target project count every 3–5 seconds, up to 5 attempts, until `count` matches the expected batch size
3. Only move on to the next batch once confirmed
4. If a copy fails to verify after 5 attempts, stop and alert the user — do not proceed

Report after each confirmed copy:
`✓ Group A → {name} ({id}): {count} contacts`

### Step 7: Verify All Target Projects

Before any deletion, re-check `count` on every target project one final time and confirm all expected counts are correct. If anything looks off, stop and alert the user.

**Do not proceed to Step 8 until every target project is confirmed.**

### Step 8: Execute Cleanup (only after Step 7 passes)

**Auto-create mode:** Delete original source project (`DELETE /projects/{source_id}`).
**Existing projects mode:** Delete the copied contacts from the source project via mass-delete, then verify the source project's remaining count equals 1 batch.

### Step 9: Report Summary

```
A/B split complete ✓

| Group | Project Name         | Project ID | Contacts |
|-------|----------------------|------------|----------|
| A     | {name}_version_a     | {id}       | {count}  |
| B     | {name}_version_b     | {id}       | {count}  |
| ...   | ...                  | ...        | ...      |

Original project: DELETED  (auto-create mode)
                  {count} contacts retained as Group {X}  (existing mode)
```

---

## API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/projects/{id}` | Fetch project name + timezone |
| `POST` | `/projects` | Create new project (`name`, `timezone`) |
| `GET` | `/projects/{id}/people` | List contacts (paginated) |
| `POST` | `/projects/{id}/copy-contacts` | Copy a batch to target project |
| `POST` | `/projects/{id}/persons/mass-delete/` | Delete contacts from a project |
| `DELETE` | `/projects/{id}` | Delete entire project |
| `GET` | `/projects/{id}/people?page=1&page_size=1` | Verify post-copy count |

**Base URL:** `https://app.leadspicker.com/app/sb/api`

**Auth header:** `x-api-key: {api_key}`

---

## Error Handling

| HTTP Status | Likely Cause | Resolution |
|-------------|--------------|------------|
| `401 Unauthorized` | Bad or expired API key | Verify `x-api-key` with user (last 6 chars) |
| `404 Not Found` | Wrong `project_id` | Confirm project ID with user |
| `422 Unprocessable` | Missing `unselected_ids` field | Always include `unselected_ids` in copy/delete payloads |
| `409 Conflict` | Project name already exists | Append `_2` to the version name or ask user for a different base name |
| `429 Too Many Requests` | Rate limit | Add 1–2s delay between API calls |

---

## Security

- **Never log or display** the full API key — confirm only the last 6 characters
- Always show the full plan (including the cleanup/deletion step) and get explicit approval before executing
- The DELETE operation on a project is irreversible — confirm with the user before proceeding
