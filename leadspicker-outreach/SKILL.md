---
name: leadspicker-outreach
description: >
  Triggers on: "sequence", "outreach", "campaign", "email sequence", "LinkedIn sequence",
  "multi-channel", "follow-up", "sekvence", "kampaň", "oslovení", "cold email",
  "connection request", "inmail", "message sequence"
---

# Leadspicker Outreach Skill

## Overview

This skill creates outreach sequences (email, LinkedIn, or multi-channel) for Leadspicker projects via the Sequence API. Sequences are built step-by-step, where each step chains to the previous one via `parent_relation`.

**Three sequence types:**
1. **Email Sequence** — cold email with follow-ups in the same thread
2. **LinkedIn Sequence** — connection check → messages or connection request → messages/InMail
3. **Multi-Channel Sequence** — combines email + LinkedIn in one sequence

## API Reference

**Base URL:** `https://app.leadspicker.com/app/sb/api`
**Auth header:** `x-api-key: {api_key}`

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sequence?force_save=true` | POST | Create a sequence step |
| `/sequence?project_id={id}` | GET | List all steps in a sequence |
| `/projects/{id}/sequence` | DELETE | Delete entire sequence |

### ⚠️ Step Types — Use EXACTLY These Values

| Step | `outreach_step_type` | Notes |
|------|---------------------|-------|
| Boolean condition gate | `"magic_column_condition"` | Root step. Only contacts matching ALL boolean columns proceed. Uses `preconditions` field. |
| Email | `""` (EMPTY STRING) | NOT "email" — empty string |
| Delay / Wait | `"delay"` | NOT "wait" or "wait_availability" |
| Check 1st degree connection | `"first_degree_connection"` | Conditional: YES (connected) / NO (not connected) |
| Send connection request | `"connect"` | NOT "connection_request" |
| Wait for acceptance | `"after_connection"` | Conditional: YES (accepted) / NO (not accepted). Uses `delay_days` for max wait |
| LinkedIn message (DM) | `"message"` | Only works with connected contacts |
| InMail | `"inmail_message"` | NOT "inmail". Premium LinkedIn only — ask user first |

### Boolean Condition Gate (magic_column_condition)

**Always add this as the FIRST step (root) of every sequence** when boolean classification columns exist in the project (e.g., "Is Relevant Position", "Is Relevant Company", "Is Target Size", "Is Target Country").

This step filters contacts — only those where ALL specified boolean columns are `true` will proceed through the sequence. Contacts that don't match are skipped entirely.

**IMPORTANT: Each condition is a SEPARATE step with ONE precondition. Multiple conditions are chained together, each connected via `relation_type: "yes"`.**

**Step payload (one condition):**
```json
{
  "project_id": {project_id},
  "outreach_step_type": "magic_column_condition",
  "is_reply": true,
  "subject": "",
  "message": "",
  "preconditions": [{column_header_id}],
  "position": {"x": 220, "y": 180}
}
```

**Chaining multiple conditions:**
```
Condition 1 (root, no parent) → preconditions: [id_1]
  → [YES] Condition 2 → preconditions: [id_2]
    → [YES] Condition 3 → preconditions: [id_3]
      → [YES] Email 1 → rest of sequence
```

Each subsequent condition uses `parent_relation: {"parent": previous_condition_id, "relation_type": "yes"}`.

**Example with 3 boolean columns:**
```python
# Step 1: First condition (root)
c1 = create_step({
    "outreach_step_type": "magic_column_condition",
    "preconditions": [380903],  # Is Relevant Position
    "position": {"x": 220, "y": 180}
})

# Step 2: Second condition (chained from C1)
c2 = create_step({
    "outreach_step_type": "magic_column_condition",
    "preconditions": [380901],  # Is Relevant Company
    "parent_relation": {"parent": c1, "relation_type": "yes"},
    "position": {"x": 220, "y": 350}
})

# Step 3: Third condition (chained from C2)
c3 = create_step({
    "outreach_step_type": "magic_column_condition",
    "preconditions": [380904],  # Is Target Size
    "parent_relation": {"parent": c2, "relation_type": "yes"},
    "position": {"x": 220, "y": 520}
})

# Step 4: First email (chained from C3 YES)
email1 = create_step({
    "outreach_step_type": "",
    "parent_relation": {"parent": c3, "relation_type": "yes"},
    ...
})
```

**Key fields:**
- `preconditions`: Array with exactly **ONE integer column header ID** per step
- Each condition connects to the next via `parent_relation` with `relation_type: "yes"`
- The first condition is the root step (no `parent_relation`)
- The last condition's YES branch connects to the first email/message step

**How to find column header IDs:**
1. Fetch the project details: `GET /projects/{project_id}`
2. Look in the `headers_data` array for boolean columns (`is_boolean: true`)
3. Use the `id` field from each matching header

```python
resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=HEADERS)
project = resp.json()
boolean_columns = [
    {"id": h["id"], "name": h["column_name"]}
    for h in project["headers_data"]
    if h.get("is_boolean") and h["id"] is not None
]
```

**Which columns to include:**
All boolean filter columns created during classification. Typical columns:
- `Is Relevant Position` — position matches target persona
- `Is Relevant Company` — company matches target industry
- `Is Target Size` — company size within range
- `Is Target Country` — location matches target geography

### Parent Relation (Step Chaining)

Every step after the root must have `parent_relation`:

```json
"parent_relation": {"parent": step_id, "relation_type": ""}
```

- Field is `parent` — **NOT** `parent_id`
- `relation_type` values:
  - `""` — default/sequential flow
  - `"yes"` — positive branch (connected / accepted)
  - `"no"` — negative branch (not connected / not accepted)

### Position (Visual Layout)

```json
"position": {"x": 220, "y": 180}
```

Visual coordinates in the sequence builder UI. Increment `y` by ~160-170 for each subsequent step. Use different `x` values for branches (e.g., YES branch at x=60, NO branch at x=380).

---

## Sequence Type 1: Email Sequence

### Structure

```
EMAIL 1 (root, is_reply=false) — new thread
  → DELAY (e.g., 3 days)
    → EMAIL 2 (is_reply=true) — same thread
      → DELAY (e.g., 3 days)
        → EMAIL 3 (is_reply=true) — same thread
```

### Step-by-Step API Calls

**Step 1: First Email (root)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "{subject_line}",
  "message": "<div>{email_body_html}</div>",
  "is_reply": false,
  "position": {"x": 220, "y": 180}
}
```

**Step 2: Delay**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step1_id}, "relation_type": ""},
  "position": {"x": 220, "y": 350}
}
```

**Step 3: Follow-up Email (same thread)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{follow_up_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step2_id}, "relation_type": ""},
  "position": {"x": 220, "y": 520}
}
```

**Step 4: Delay**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step3_id}, "relation_type": ""},
  "position": {"x": 220, "y": 690}
}
```

**Step 5: Final Follow-up Email (same thread)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{final_follow_up_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step4_id}, "relation_type": ""},
  "position": {"x": 220, "y": 860}
}
```

### Email Step Key Fields

| Field | Value | Notes |
|-------|-------|-------|
| `outreach_step_type` | `""` | Empty string for email |
| `subject` | `"Subject line"` | Only on first email (`is_reply: false`) |
| `message` | `"<div>HTML</div>"` | HTML format — same field as LinkedIn, but uses HTML for emails |
| `is_reply` | `false` / `true` | `false` = new thread, `true` = same thread |

---

## Sequence Type 2: LinkedIn Sequence

### Structure

```
FIRST_DEGREE_CONNECTION (root) — check if already connected
├── YES (already connected):
│   ├── MESSAGE 1 (DM)
│   ├── DELAY
│   └── MESSAGE 2 (follow-up DM)
│
└── NO (not connected):
    ├── CONNECT (send connection request)
    ├── AFTER_CONNECTION (wait up to 7 days for acceptance)
    ├── YES (accepted):
    │   ├── MESSAGE 1 (DM)
    │   ├── DELAY
    │   └── MESSAGE 2 (follow-up DM)
    └── NO (not accepted):
        └── INMAIL_MESSAGE (premium only)
```

### Step-by-Step API Calls

**Step 1: Check 1st Degree Connection (root)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "first_degree_connection",
  "is_reply": true,
  "subject": "",
  "message": "",
  "position": {"x": 220, "y": 180}
}
```

#### YES Branch (Already Connected)

**Step 2: LinkedIn Message (YES branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{message_subject}",
  "message": "{message_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step1_id}, "relation_type": "yes"},
  "position": {"x": 60, "y": 370}
}
```

**Step 3: Delay (YES branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step2_id}, "relation_type": ""},
  "position": {"x": 60, "y": 530}
}
```

**Step 4: Follow-up Message (YES branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{follow_up_subject}",
  "message": "{follow_up_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step3_id}, "relation_type": ""},
  "position": {"x": 60, "y": 690}
}
```

#### NO Branch (Not Connected)

**Step 5: Send Connection Request (NO branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "connect",
  "is_reply": true,
  "subject": "LinkedIn connection request",
  "message": "",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step1_id}, "relation_type": "no"},
  "position": {"x": 380, "y": 370}
}
```

**Step 6: Wait for Connection Acceptance**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "after_connection",
  "is_reply": true,
  "subject": "",
  "message": "",
  "delay_days": 7,
  "delay_hours": 0,
  "parent_relation": {"parent": {step5_id}, "relation_type": ""},
  "position": {"x": 380, "y": 560}
}
```

**Step 7: Message After Acceptance (YES)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{message_subject}",
  "message": "{message_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step6_id}, "relation_type": "yes"},
  "position": {"x": 280, "y": 750}
}
```

**Step 8: Delay After Acceptance**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 2,
  "delay_hours": 0,
  "parent_relation": {"parent": {step7_id}, "relation_type": ""},
  "position": {"x": 280, "y": 910}
}
```

**Step 9: Final Follow-up Message**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{final_subject}",
  "message": "{final_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step8_id}, "relation_type": ""},
  "position": {"x": 280, "y": 1070}
}
```

**Step 10: InMail (Connection NOT Accepted — NO)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "inmail_message",
  "is_reply": true,
  "subject": "{inmail_subject}",
  "message": "{inmail_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step6_id}, "relation_type": "no"},
  "position": {"x": 500, "y": 750}
}
```

### LinkedIn Step Key Fields

| Field | Value | Notes |
|-------|-------|-------|
| `message` | `"text"` | LinkedIn message body (plain text, not HTML) |
| `subject` | `"text"` | Message subject line |
| `delay_days` | `1` | Minimum delay before sending (on message steps) |
| `delay_hours` | `0` | Additional hours delay |

### InMail — Premium Only

Before adding an `inmail_message` step, **always ask the user** if they have LinkedIn Premium. Non-premium users cannot send InMails. If the user is not premium, skip the InMail step entirely.

---

## Sequence Type 3: Multi-Channel (Email + LinkedIn)

### ⚠️ MANDATORY: Always Check 1st Degree Connection

**NEVER skip `first_degree_connection` in multi-channel sequences.** This step MUST come before any LinkedIn connect/message steps. Without it, you risk sending connection requests to people who are already connected, which looks unprofessional and wastes LinkedIn actions.

**Also note:** `first_degree_connection` is a BRANCHING step — it ONLY supports `yes` and `no` children. You CANNOT attach a default `""` relation child to it. Each branch (YES/NO) must contain its own complete follow-up chain (including email follow-ups).

### Structure

```
CONDITION GATE (root) — checks all boolean columns, only matching contacts proceed
  → [YES] EMAIL 1 (is_reply=false) — new thread
    → DELAY (3 days)
    → FIRST_DEGREE_CONNECTION — check if already connected
      ├── YES (already connected):
      │   → MESSAGE 1 (DM)
      │     → DELAY (3 days)
      │       → MESSAGE 2 (follow-up DM)
      │         → DELAY (3 days)
      │           → EMAIL fallback (is_reply=true, same thread)
      │
      └── NO (not connected):
          → CONNECT (send connection request)
            → AFTER_CONNECTION (wait up to 7 days)
              ├── YES (accepted):
              │   → MESSAGE 1 (DM)
              │     → DELAY (3 days)
              │       → MESSAGE 2 (follow-up DM)
              │         → DELAY (3 days)
              │           → EMAIL fallback (is_reply=true, same thread)
              │
              └── NO (not accepted):
                  → INMAIL_MESSAGE (optional, premium only)
                    → DELAY (3 days)
                      → EMAIL fallback (is_reply=true, same thread)
```

**Without LinkedIn Premium (no InMail):** The NO-not-accepted branch skips InMail and goes directly to the email fallback:
```
              └── NO (not accepted):
                  → EMAIL fallback (is_reply=true, same thread)
```

### ⚠️ InMail is Optional — Ask About LinkedIn Premium

Before building a multi-channel sequence, **always ask the user** if they have LinkedIn Premium:
- **Premium user** → include InMail step in the NO-not-accepted branch (18 steps total)
- **Non-premium user** → skip InMail, email fallback connects directly to `after_connection` NO branch (16 steps total)

### Step-by-Step API Calls (With InMail — 18 Steps)

#### Email Phase (1 email → delay)

**Step 1: First Email (root)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "{subject_line}",
  "message": "<div>{email_body_html}</div>",
  "is_reply": false,
  "position": {"x": 220, "y": 180}
}
```

**Step 2: Delay (3 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step1_id}, "relation_type": ""},
  "position": {"x": 220, "y": 350}
}
```

#### LinkedIn Phase — Connection Check

**Step 3: Check 1st Degree Connection**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "first_degree_connection",
  "is_reply": true,
  "subject": "",
  "message": "",
  "parent_relation": {"parent": {step2_id}, "relation_type": ""},
  "position": {"x": 220, "y": 520}
}
```

#### YES Branch — Already Connected (x=60)

**Step 4: LinkedIn Message 1 (YES branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{message_subject}",
  "message": "{message_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step3_id}, "relation_type": "yes"},
  "position": {"x": 60, "y": 690}
}
```

**Step 5: Delay (3 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step4_id}, "relation_type": ""},
  "position": {"x": 60, "y": 860}
}
```

**Step 6: LinkedIn Message 2 (follow-up)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{follow_up_subject}",
  "message": "{follow_up_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step5_id}, "relation_type": ""},
  "position": {"x": 60, "y": 1030}
}
```

**Step 7: Delay (3 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step6_id}, "relation_type": ""},
  "position": {"x": 60, "y": 1200}
}
```

**Step 8: Email Fallback (same thread as Step 1)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{email_fallback_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step7_id}, "relation_type": ""},
  "position": {"x": 60, "y": 1370}
}
```

#### NO Branch — Not Connected (x=380)

**Step 9: Send Connection Request (NO branch)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "connect",
  "is_reply": true,
  "subject": "LinkedIn connection request",
  "message": "",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step3_id}, "relation_type": "no"},
  "position": {"x": 380, "y": 690}
}
```

**Step 10: Wait for Connection Acceptance (up to 7 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "after_connection",
  "is_reply": true,
  "subject": "",
  "message": "",
  "delay_days": 7,
  "delay_hours": 0,
  "parent_relation": {"parent": {step9_id}, "relation_type": ""},
  "position": {"x": 380, "y": 860}
}
```

#### NO-YES Branch — Connection Accepted (x=280)

**Step 11: LinkedIn Message 1 (after acceptance)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{message_subject}",
  "message": "{message_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step10_id}, "relation_type": "yes"},
  "position": {"x": 280, "y": 1030}
}
```

**Step 12: Delay (3 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step11_id}, "relation_type": ""},
  "position": {"x": 280, "y": 1200}
}
```

**Step 13: LinkedIn Message 2 (follow-up)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "message",
  "is_reply": true,
  "subject": "{follow_up_subject}",
  "message": "{follow_up_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step12_id}, "relation_type": ""},
  "position": {"x": 280, "y": 1370}
}
```

**Step 14: Delay (3 days)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step13_id}, "relation_type": ""},
  "position": {"x": 280, "y": 1540}
}
```

**Step 15: Email Fallback (same thread as Step 1)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{email_fallback_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step14_id}, "relation_type": ""},
  "position": {"x": 280, "y": 1710}
}
```

#### NO-NO Branch — Connection NOT Accepted (x=500)

**⚠️ Steps 16-17 are OPTIONAL — only include if user has LinkedIn Premium**

**Step 16: InMail (optional, premium only)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "inmail_message",
  "is_reply": true,
  "subject": "{inmail_subject}",
  "message": "{inmail_body}",
  "delay_days": 1,
  "delay_hours": 0,
  "parent_relation": {"parent": {step10_id}, "relation_type": "no"},
  "position": {"x": 500, "y": 1030}
}
```

**Step 17: Delay (3 days) (optional, only with InMail)**
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "delay",
  "delay_days": 3,
  "delay_hours": 0,
  "parent_relation": {"parent": {step16_id}, "relation_type": ""},
  "position": {"x": 500, "y": 1200}
}
```

**Step 18: Email Fallback (same thread as Step 1)**

If user has Premium (InMail included):
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{email_fallback_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step17_id}, "relation_type": ""},
  "position": {"x": 500, "y": 1370}
}
```

If user does NOT have Premium (no InMail — email connects directly to after_connection NO):
```json
POST /sequence?force_save=true

{
  "project_id": {project_id},
  "outreach_step_type": "",
  "subject": "",
  "message": "<div>{email_fallback_body_html}</div>",
  "is_reply": true,
  "parent_relation": {"parent": {step10_id}, "relation_type": "no"},
  "position": {"x": 500, "y": 1030}
}
```

### Multi-Channel Key Differences from LinkedIn-Only

| Aspect | LinkedIn Sequence | Multi-Channel Sequence |
|--------|------------------|----------------------|
| Root step | `first_degree_connection` | Email (new thread) |
| Email phase | None | 1 email → delay before LinkedIn |
| Terminal steps | Messages / InMail | Email fallback (same thread) on every branch |
| `is_reply` on fallback emails | N/A | `true` — continues the thread from Step 1 |
| Total steps (with InMail) | 10 | 18 |
| Total steps (without InMail) | 9 | 16 |

---

## Message Generation — BASHO-Style Outreach

### Philosophy

All outreach messages follow the **BASHO approach**: short, relevant, trigger-led messages that read like a real person wrote them. Leadspicker never generates generic templates — every message is tied to a specific reason for reaching out.

**Core principles:**
- **Relevance beats personalization.** "Congrats on…" isn't enough. Tie the message to *why now*.
- **One idea per email/message.** Don't stack problems, features, and asks.
- **Mobile-first.** Short lines, lots of white space, fast to understand.
- **Write like you talk.** Simple words, short sentences.
- **No cheesy openers.** NEVER use "I hope you're doing well", "I hope this finds you well", or any similar throat-clearing phrases.

### Pre-Generation Checklist

Before generating any outreach messages, **always complete these steps in order:**

1. **Ask the user what they're selling/offering** — What is the product, service, or purpose of the outreach? What problem does it solve? Who is the ICP (Ideal Customer Profile)?
2. **Ask for preferred language** — Default is English. If non-English, all messages will be written in the target language.
3. **Ask about LinkedIn Premium** — Determines connection request text (blank vs. 200 chars) and InMail availability.
4. **For LinkedIn / Multi-Channel: Ask the user for their sender name** — LinkedIn messages don't have auto-signature. Ask: "What name should I sign the LinkedIn messages with?" Use the exact name they provide (e.g., "Tomáš" or "Tomáš Blaťák"), NOT recipient variables.
5. **Fetch available variables** — `GET /projects/{id}/people?page=1&page_size=5` to see all columns. Check for:
   - Standard fields: `{{first_name}}`, `{{last_name}}`, `{{full_name}}`, `{{position}}`, `{{company_name}}`
   - Enrichment columns: `{{linkedin_company_description}}`, `{{website_text_summary}}`, `{{linkedin_about_me}}`
   - **Personalization columns** (from personalizer skill): `{{website_hook}}`, `{{company_hook}}`, `{{experience_hook}}`, `{{icebreaker}}`, `{{salutation}}`, etc.
   - Any custom AI columns created by the classifier/personalizer
6. **Use personalization variables** — If hooks/icebreakers exist as columns, incorporate them into messages. These are pre-generated short fragments designed to fit naturally into outreach.

### Message Structure (BASHO Framework)

Every outreach message follows this 4-part structure:

**1) Opener = "Reason I'm reaching out"** (1-2 lines)
- Sales trigger (funding, hiring, new product, leadership change, expansion)
- Observation (something specific on their site, pricing, messaging, reviews, job posts)
- Peer signal (competitor/adjacent brand doing X)
- Or use a pre-generated personalization variable: `{{website_hook}}`, `{{icebreaker}}`
- Goal: establish "this isn't a template" immediately.

**2) Reframe = Make them think** (1-2 lines)
- Pattern interrupt question: "Curious if you're seeing X…"
- Simple outcome statement: "Teams use us to reduce X / improve Y without Z."
- Goal: create curiosity without pitching features.

**3) Proof = "Others like you succeeded"** (1 line)
- "Teams like [type] are seeing…"
- "We helped a similar [industry] team…"
- "Commonly we see X within Y weeks…"
- Goal: reduce perceived risk fast. 1 line max, no case study essays.

**4) CTA = Low-friction next step** (1 line)
- NOT "book a demo" — instead:
  - "Worth a 10-min chat to compare notes?"
  - "Open to me sending over a quick teardown?"
  - "Should I speak with you or someone else on this?"
- Goal: make "yes" easy. One clear CTA only.

### Word Count Limits

| Step Type | Word Count | Notes |
|-----------|-----------|-------|
| **Initial email** (`is_reply: false`) | 150–200 words | Full BASHO structure (opener + reframe + proof + CTA) |
| **Second follow-up email** (`is_reply: true`) | 100–150 words | Slightly shorter, adds one new insight/proof |
| **Final follow-up email** (`is_reply: true`) | 50–100 words | Breakup style, close-the-loop |
| **LinkedIn DM** (`message`) | 150–200 words | Same depth as email, full BASHO structure |
| **LinkedIn follow-up DM** | 100–150 words | Adds new value, shorter |
| **LinkedIn connection request** (non-premium) | **BLANK** | Non-premium users get only 5 messages/month — leave empty |
| **LinkedIn connection request** (premium) | Max 200 characters | Very short, trigger + relevance only |
| **InMail** (`inmail_message`) | 150–200 words | Full BASHO structure, subject line required |
| **Email fallback** (multi-channel, `is_reply: true`) | 50–100 words | Breakup style, references previous LinkedIn outreach |

### Follow-Up Rules

**Second follow-up** (100–150 words):
- NOT "bumping this" or "just following up"
- Add something NEW: a sharper insight, a tiny teardown, a relevant example
- Reference the previous message briefly, then pivot to new value

**Final follow-up / breakup** (50–100 words):
- Polite close-the-loop message
- Style: "If the timing isn't right, no worries — just wanted to close the loop"
- Give them an easy out while leaving the door open
- Can include one final micro-value or observation

### Spintax Format

Use spintax `{option1 | option2 | option3}` for text rotation in every message.

**Required spintax locations:**
1. **Greeting** — always: `{Hi | Hey | Hello}`, or language-specific: `{Dobrý den | Zdravím}`
2. **Closing** — always: `{Best | Cheers | Kind regards | Thanks}`, or language-specific: `{S pozdravem | Díky | Přeji hezký den}`

**Additional spintax** (2-4 more places per message):
- Opener phrasing: `{I noticed | I saw | Caught my eye that}`
- Reframe: `{Curious if | Wondering whether | Quick question —}`
- Proof intro: `{Teams like yours | Similar companies | Others in your space}`
- CTA phrasing: `{Worth a quick chat? | Open to connecting? | Would 10 minutes make sense?}`
- Transitions: `{That said | With that in mind | On that note}`

**Total: at least 4-6 spintax locations per message** (2 required + 2-4 additional).

### Subject Line Rules

Subject lines use spintax for rotation. Keep them short (3-8 words), curiosity-driven, no clickbait.

Examples:
```
{Quick question | Thought about this | Noticed something} about {{company_name}}
{{{first_name}} | Quick thought} — {{company_name}}
{Idea for | Question about | Observation on} {{company_name}}
```

Only the first email (`is_reply: false`) has a subject line. All follow-ups (`is_reply: true`) have an empty subject (they continue the same thread).

### LinkedIn Premium Rules

**Non-premium user:**
- Connection request message = **BLANK** (empty string). Non-premium users can only send 5 connection requests with a message per month — it doesn't make sense to use text there.
- No InMail step — skip entirely.
- Total: LinkedIn sequence has 9 steps, multi-channel has 16 steps.

**Premium user:**
- Connection request message = max **200 characters**. Short trigger + relevance. Example: `"Hi {{first_name}}, {{website_hook}} — would love to connect and share thoughts."`
- InMail is available — include with subject line + full BASHO message (150-200 words).
- Total: LinkedIn sequence has 10 steps, multi-channel has 18 steps.

### Variable Usage in Messages

Always check which columns exist before generating messages. Use personalization variables when available:

**Priority order for openers:**
1. `{{icebreaker}}` — if LinkedIn posts icebreaker exists (most personal)
2. `{{website_hook}}` — if website hook exists (company-specific)
3. `{{company_hook}}` — if company LinkedIn hook exists
4. `{{experience_hook}}` — if experience hook exists (person-specific)
5. Manual trigger based on `{{position}}` + `{{company_name}}` (fallback)

**Always available variables:**
- `{{first_name}}`, `{{last_name}}`, `{{full_name}}`
- `{{company_name}}`, `{{position}}`

**Use if enriched:**
- `{{linkedin_company_description}}`, `{{website_text_summary}}`
- `{{linkedin_about_me}}`, `{{present_experiences}}`

**Use if personalized (from personalizer skill):**
- `{{website_hook}}`, `{{company_hook}}`, `{{experience_hook}}`, `{{icebreaker}}`
- `{{salutation}}` (for language-specific greetings)

### Message Writing Rules (The Hard Rules)

1. **Under ~150-200 words** for initial messages, shorter for follow-ups
2. **No "hope you're well"** / no throat-clearing / no cheesy openers
3. **No feature dump** — talk outcomes and the "problem you solve"
4. **Specificity wins**: numbers, timeframes, scope (when you can)
5. **One clear CTA** (not multiple questions)
6. **Avoid spam signals**: too many links, heavy formatting, buzzwords, exclamation marks
7. **Write like you talk**: simple words, short sentences
8. **Make it skimmable**: 1-2 lines per paragraph, 3-6 short paragraphs
9. **3-6 short paragraphs** — lots of white space
10. **Mobile-first** — short lines that look good on phone screens
11. **Each follow-up adds something new** — never just "bumping this"
12. **Final follow-up is breakup style** — close the loop politely
13. **Emails: NO sender name/signature** — Leadspicker auto-appends the email signature. Do not include closing name or signature in email messages.
14. **LinkedIn: ALWAYS include sender's real name** — LinkedIn has no auto-signature. End every LinkedIn message with the user's actual name (asked in pre-generation checklist). Never use recipient variables for the sender name.

### Multi-Language Support

- **Default language**: English
- **Always ask** the user for preferred language before generating messages
- **Spintax in target language**: greetings, closings, and other spintax elements must be in the target language
- **If salutation column exists** (from personalizer skill): use `{{salutation}}` instead of generic greeting spintax
- **Native phrasing**: messages should read naturally in the target language, not like translations

### Email Body Format

Emails use HTML in the `message` field. Use `<div>` and `<br>` for structure.

**⚠️ Do NOT include sender name or signature in email messages.** Leadspicker automatically appends the sender's email signature to every email. Adding a name/signature in the message body would result in duplicate signatures.

```html
<div>
{Hi | Hey | Hello} {{first_name}},<br><br>
{{website_hook}}<br><br>
{Curious if | Wondering whether} you're seeing similar challenges with [problem].<br><br>
{Teams like yours | Similar companies in {{industry}}} are seeing [outcome] within [timeframe].<br><br>
{Worth a quick 10-min chat? | Open to comparing notes?}
</div>
```

### LinkedIn Message Format

LinkedIn messages use plain text in the `message` field (NOT HTML).

**⚠️ LinkedIn messages do NOT have auto-signature.** Always include the sender's real name at the end of every LinkedIn message. **Ask the user for their actual name** before generating LinkedIn messages — do NOT use variables like `{{first_name}}` or `{{full_name}}` (those are the *recipient's* data). Use the exact name the user provides.

```
{Hi | Hey | Hello} {{first_name}},

{{website_hook}}

{Curious if | Wondering whether} you're exploring [topic] — {teams like yours | others in your space} are seeing [outcome].

{Worth connecting to share notes? | Open to a quick chat?}

{Best | Cheers},
{user's actual name}
```

---

## Workflow

1. **Collect input**: project_id, api_key, sequence type (email / LinkedIn / multi-channel)
2. **Check existing sequence**: `GET /sequence?project_id={id}` — warn if sequence already exists
3. **Ask what the user is selling/offering**: product, service, value proposition, ICP, problem solved
4. **Ask for preferred language**: default English, messages in target language if non-English
5. **For LinkedIn or Multi-Channel**: Ask if user has LinkedIn Premium (for InMail step + connection request text). If non-premium, skip InMail and leave connection request blank
6. **For LinkedIn or Multi-Channel**: Ask for the user's sender name to sign LinkedIn messages (e.g., "What name should I sign the LinkedIn messages with?")
7. **Fetch available variables**: `GET /projects/{id}/people?page=1&page_size=5` — check all columns including personalization hooks
8. **Generate messages**: Write all step texts following BASHO framework, word limits, spintax rules, and available variables. For emails: no sender name (auto-signature). For LinkedIn: use the sender name from step 6.
9. **Show messages to user for approval**: Display all generated texts before building the sequence
10. **Build sequence**: Execute POST calls step-by-step, chaining via parent_relation, with approved message texts
11. **Verify**: `GET /sequence?project_id={id}` — show the complete sequence tree
12. **Confirm with user**: Show the final sequence structure

## Deleting a Sequence

To start over, delete the entire sequence:

```
DELETE /projects/{project_id}/sequence
```

This removes ALL steps. There is no way to delete individual steps — only the entire sequence.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Graph Invalid" | Missing `parent_relation` on non-root step | Add `parent_relation` with correct parent ID |
| "Field required" for `parent` | Used `parent_id` instead of `parent` | Use `parent` field name |
| "Input should be '', 'yes' or 'no'" | Invalid `relation_type` | Use `""`, `"yes"`, or `"no"` only |
| Step created but wrong type in UI | Wrong `outreach_step_type` value | See step types table above |

## Security

- Never store or log the API key
- Always read the API key from user input or `.env` file
- The API key goes in the `x-api-key` header, never in URLs

## Natural Language Matching

| User says (EN) | User says (CZ) | Action |
|----------------|----------------|--------|
| "create email sequence" | "vytvoř emailovou sekvenci" | Build Email Sequence (ask for offer/ICP first) |
| "create LinkedIn sequence" | "vytvoř LinkedIn sekvenci" | Build LinkedIn Sequence (ask for offer/ICP + Premium) |
| "create multi-channel sequence" | "vytvoř multi-channel sekvenci" | Build Multi-Channel Sequence (ask for offer/ICP + Premium) |
| "3 emails with 3 day delays" | "3 emaily s 3denními pauzami" | Email: 3 emails + 2 delays of 3 days |
| "LinkedIn outreach with InMail" | "LinkedIn oslovení s InMailem" | LinkedIn with InMail (ask about Premium) |
| "write outreach messages" | "napiš oslovení" | Generate BASHO-style messages for existing sequence |
| "create campaign for [product]" | "vytvoř kampaň pro [produkt]" | Full sequence + messages (ask for language + Premium) |
| "delete sequence" | "smaž sekvenci" | Delete entire sequence |
| "show sequence" | "ukaž sekvenci" | GET and display sequence |
