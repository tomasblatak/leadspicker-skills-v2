---
name: leadspicker-outreach
description: >
  Triggers on: "sequence", "outreach", "campaign", "email sequence", "LinkedIn sequence",
  "multi-channel", "follow-up", "sekvence", "kampaň", "oslovení", "cold email",
  "connection request", "inmail", "message sequence"
---

# Leadspicker Outreach Skill

## Overview

This skill creates outreach sequences (email, LinkedIn, or multi-channel) for Leadspicker projects via the Sequence API. An entire sequence is created in a single API call using `POST /projects/{project_id}/sequence`.

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
| `/projects/{id}/sequence?force_save=true` | POST | **Create entire sequence in one call** |
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

Add conditions as the first steps when boolean classification columns exist in the project. Conditions can also be placed mid-sequence. Each condition is a separate step with one `condition` array containing a single header ID.

**Chaining conditions in batch payload:**
```json
"check-icp": {
  "outreach_step_type": "magic_column_condition",
  "condition": [387407]
},
"check-company": {
  "outreach_step_type": "magic_column_condition",
  "condition": [387411],
  "parents": [{"parent": "check-icp", "relation_type": "yes"}]
}
```

**How to find column header IDs:**
1. Fetch: `GET /projects/{project_id}`
2. Look in `headers_data` for entries where `is_boolean: true`
3. Use the `id` field

### Parent References (Batch Endpoint)

In the batch endpoint, steps reference parents by named string keys or existing numeric IDs:

```json
"parents": ["delay-step"]                                      // simple chain
"parents": [{"parent": "wait-accept", "relation_type": "yes"}] // YES branch
"parents": [{"parent": 4567, "relation_type": ""}]             // existing step ID
```

- `relation_type`: `""` (sequential), `"yes"` (positive branch), `"no"` (negative branch)
- Root steps have no `parents` field
- Position is auto-calculated — no need to set coordinates

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

### Batch API Call

```bash
POST /projects/{project_id}/sequence?force_save=true
```

```json
{
  "sequence_messages": {
    "email-1": {
      "subject": "{subject_line}",
      "message": "<div>{email_body_html}</div>",
      "outreach_step_type": "",
      "is_reply": false
    },
    "delay-1": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["email-1"]
    },
    "email-2": {
      "subject": "Re: {subject_line}",
      "message": "<div>{follow_up_body_html}</div>",
      "outreach_step_type": "",
      "is_reply": true,
      "parents": ["delay-1"]
    },
    "delay-2": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["email-2"]
    },
    "email-3": {
      "subject": "Re: {subject_line}",
      "message": "<div>{final_follow_up_body_html}</div>",
      "outreach_step_type": "",
      "is_reply": true,
      "parents": ["delay-2"]
    }
  }
}
```

### Email Step Key Fields

| Field | Value | Notes |
|-------|-------|-------|
| `outreach_step_type` | `""` | Empty string for email |
| `subject` | `"Subject line"` | First email: original subject. Follow-ups: `"Re: {subject}"` |
| `message` | `"<div>HTML</div>"` | HTML format |
| `is_reply` | `false` / `true` | `false` = new thread, `true` = same thread |

---

## Sequence Type 2: LinkedIn Sequence

### Structure

```
CONNECT (root) — send connection request
  → AFTER_CONNECTION (wait up to 7 days)
    ├── YES (accepted):
    │   → MESSAGE 1 → DELAY → MESSAGE 2
    └── NO (not accepted):
        → INMAIL (premium only) → DELAY → INMAIL 2
```

### Batch API Call

```bash
POST /projects/{project_id}/sequence?force_save=true
```

```json
{
  "sequence_messages": {
    "connect": {
      "message": "{connection_request_text}",
      "outreach_step_type": "connect"
    },
    "wait-accept": {
      "outreach_step_type": "after_connection",
      "delay_days": 7,
      "parents": ["connect"]
    },
    "accepted-msg-1": {
      "message": "{message_body_1}",
      "outreach_step_type": "message",
      "parents": [{"parent": "wait-accept", "relation_type": "yes"}]
    },
    "accepted-delay": {
      "outreach_step_type": "delay",
      "delay_days": 5,
      "parents": ["accepted-msg-1"]
    },
    "accepted-msg-2": {
      "message": "{follow_up_body}",
      "outreach_step_type": "message",
      "parents": ["accepted-delay"]
    },
    "not-accepted-inmail-1": {
      "subject": "{inmail_subject}",
      "message": "{inmail_body}",
      "outreach_step_type": "inmail_message",
      "parents": [{"parent": "wait-accept", "relation_type": "no"}]
    },
    "not-accepted-delay": {
      "outreach_step_type": "delay",
      "delay_days": 5,
      "parents": ["not-accepted-inmail-1"]
    },
    "not-accepted-inmail-2": {
      "subject": "{inmail_subject_2}",
      "message": "{inmail_follow_up_body}",
      "outreach_step_type": "inmail_message",
      "parents": ["not-accepted-delay"]
    }
  }
}
```

### LinkedIn Step Key Fields

| Field | Value | Notes |
|-------|-------|-------|
| `message` | `"text"` | LinkedIn message body (plain text, not HTML) |
| `subject` | `"text"` | Subject line (required for InMail) |

### InMail — Premium Only

Before adding `inmail_message` steps, **always ask the user** if they have LinkedIn Premium. Non-premium: skip InMail steps entirely.

---

## Sequence Type 3: Multi-Channel (Email + LinkedIn)

### ⚠️ MANDATORY: Always Check 1st Degree Connection

**NEVER skip `first_degree_connection` in multi-channel sequences.** This step MUST come before any LinkedIn connect/message steps.

### Structure

```
CONDITIONS (optional) — filter contacts by boolean columns
  → EMAIL 1 → DELAY → FOLLOW-UP EMAIL → DELAY
    → FIRST_DEGREE_CONNECTION
      ├── YES (already connected):
      │   → MESSAGE 1 → DELAY → MESSAGE 2
      └── NO (not connected):
          → CONNECT → AFTER_CONNECTION (7 days)
            ├── YES (accepted):
            │   → MESSAGE 1 → DELAY → MESSAGE 2
            └── NO (not accepted):
                → INMAIL (premium) → DELAY → FINAL EMAIL
```

### ⚠️ InMail is Optional — Ask About LinkedIn Premium

- **Premium** → include InMail in NO-not-accepted branch
- **Non-premium** → skip InMail, use final email directly

### Batch API Call (With Conditions + InMail — 18 Steps)

```bash
POST /projects/{project_id}/sequence?force_save=true
```

```json
{
  "sequence_messages": {
    "check-icp": {
      "outreach_step_type": "magic_column_condition",
      "condition": [{boolean_header_id_1}]
    },
    "check-language": {
      "outreach_step_type": "magic_column_condition",
      "condition": [{boolean_header_id_2}],
      "parents": [{"parent": "check-icp", "relation_type": "yes"}]
    },
    "first-email": {
      "subject": "{subject_line}",
      "message": "<div>{email_body_html}</div>",
      "outreach_step_type": "",
      "is_reply": false,
      "parents": [{"parent": "check-language", "relation_type": "yes"}]
    },
    "delay-after-email-1": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["first-email"]
    },
    "followup-email": {
      "subject": "Re: {subject_line}",
      "message": "<div>{follow_up_html}</div>",
      "outreach_step_type": "",
      "is_reply": true,
      "parents": ["delay-after-email-1"]
    },
    "delay-after-email-2": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["followup-email"]
    },
    "check-connected": {
      "outreach_step_type": "first_degree_connection",
      "parents": ["delay-after-email-2"]
    },
    "already-connected-msg": {
      "message": "{li_message_for_connected}",
      "outreach_step_type": "message",
      "parents": [{"parent": "check-connected", "relation_type": "yes"}]
    },
    "already-connected-delay": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["already-connected-msg"]
    },
    "already-connected-msg-2": {
      "message": "{li_followup_for_connected}",
      "outreach_step_type": "message",
      "parents": ["already-connected-delay"]
    },
    "not-connected-request": {
      "message": "{connection_request_text}",
      "outreach_step_type": "connect",
      "parents": [{"parent": "check-connected", "relation_type": "no"}]
    },
    "wait-accept": {
      "outreach_step_type": "after_connection",
      "delay_days": 7,
      "parents": ["not-connected-request"]
    },
    "accepted-msg": {
      "message": "{li_message_after_accept}",
      "outreach_step_type": "message",
      "parents": [{"parent": "wait-accept", "relation_type": "yes"}]
    },
    "accepted-delay": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["accepted-msg"]
    },
    "accepted-msg-2": {
      "message": "{li_followup_after_accept}",
      "outreach_step_type": "message",
      "parents": ["accepted-delay"]
    },
    "not-accepted-inmail": {
      "subject": "{inmail_subject}",
      "message": "{inmail_body}",
      "outreach_step_type": "inmail_message",
      "parents": [{"parent": "wait-accept", "relation_type": "no"}]
    },
    "not-accepted-delay": {
      "outreach_step_type": "delay",
      "delay_days": 3,
      "parents": ["not-accepted-inmail"]
    },
    "final-email": {
      "subject": "{final_subject}",
      "message": "<div>{final_email_html}</div>",
      "outreach_step_type": "",
      "is_reply": false,
      "parents": ["not-accepted-delay"]
    }
  }
}
```

### Multi-Channel Key Differences from LinkedIn-Only

| Aspect | LinkedIn Sequence | Multi-Channel Sequence |
|--------|------------------|----------------------|
| Root step | `connect` | Condition gate or email |
| Email phase | None | 1-2 emails + delays before LinkedIn |
| Terminal steps | Messages / InMail | Email fallback on last branch |

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
8. **Check boolean columns**: `GET /projects/{id}` → `headers_data` where `is_boolean: true`. **If any boolean columns exist, ALWAYS add them as `magic_column_condition` steps at the root of the sequence** (chained via `relation_type: "yes"`). This ensures only qualified contacts enter the outreach flow. Skip this step only if no boolean columns exist in the project.
9. **Generate messages**: Write all step texts following BASHO framework, word limits, spintax rules, and available variables. For emails: no sender name (auto-signature). For LinkedIn: use the sender name from step 6.
10. **Show messages to user for approval**: Display all generated texts before building the sequence
11. **Delete existing sequence if any**: `DELETE /projects/{id}/sequence`
12. **Build sequence in one call**: `POST /projects/{id}/sequence?force_save=true` with the full `sequence_messages` object
13. **Verify**: `GET /sequence?project_id={id}` — show the complete sequence tree

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
