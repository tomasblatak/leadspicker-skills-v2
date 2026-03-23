---
name: leadspicker-personalizer
description: >
  Generates short personalization hooks, icebreakers, salutations, and vocatives for cold email
  campaigns in Leadspicker.com projects. Use this skill whenever the user wants
  to create personalized opening lines, hooks, greetings, salutations, vocative forms, or any
  short text fragment for outreach — for example "create a website hook", "write an icebreaker
  from LinkedIn posts", "generate Czech salutation", "personalize the opening line",
  "create vocative from first name", "napiš oslovení", "vytvoř personalizaci", "úvodní věta",
  "hook z webu", "icebreaker z příspěvků", or any request to add a personalization column to a
  Leadspicker project. Also triggers when the user mentions personalization, opening lines,
  hooks, icebreakers, greetings, formal address, vocative case, name declension, or
  multi-language salutations in the context of Leadspicker.
---

# Leadspicker Personalizer

Generates short personalization fragments for cold email campaigns in Leadspicker projects
via the magic-columns API. Each column runs GPT-5.4-Mini on every contact to produce a brief,
natural sentence fragment or grammar-correct salutation.

This skill is a companion to `leadspicker-data-enrichment` (provides the input data) and
`leadspicker-classifier` (classifies and filters contacts). It uses the enriched data
(company descriptions, website summaries, LinkedIn profiles, posts) as input for
personalization prompts.

---

## Core Philosophy

**Leadspicker never generates full messages — only short parts.**

Every personalization output is a short sentence fragment (typically **14-16 words**). This keeps
GPT-5.4-Mini focused, reduces hallucination, and gives the user full control over the
final message structure. The exact word limit can be adjusted per request.

Examples of what this skill produces:
- `"I saw your company specializes in AI-powered sales automation"` (website hook)
- `"I noticed your recent post about hiring challenges in tech"` (icebreaker)
- `"Dobrý den, pane Nováku"` (Czech salutation)
- `"Tomáši"` (Czech first name vocative)

These fragments are inserted into message templates alongside static text the user controls.

---

## User Input

Always collect (or confirm you have) these parameters before making any API calls:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `project_id` | Leadspicker project ID | `29842` |
| `api_key` | User's API key (`x-api-key`) | `fd1f0d98...` |
| Personalization request | What hook or greeting to generate | `"website hook in Czech"` |
| `column_name` | Name for the new column | `"Website Hook - CZ"` |
| Output language | Language for the output (default: English) | `"Czech"`, `"German"`, `"Polish"` |

If the user doesn't provide a `column_name`, generate one from the personalization type
and language (e.g., `"Website Hook"`, `"CZ Salutation"`, `"Icebreaker - DE"`).

---

## System Prompt (Fixed — Do Not Modify)

Every AI column in Leadspicker is wrapped by a fixed system prompt that you **cannot change**.
All personalizations use **string mode** (`is_boolean: false`).

```
System forces output: {"result": "response"}
```

**What this means for your prompts:**
- NEVER include output format instructions — the system prompt handles JSON
- Just describe the task, the rules, and provide the input variables
- The system prompt will wrap your output in `{"result": "..."}` automatically
- All personalization prompts use `is_boolean: false`

---

## Personalization Types

### A. Company-Based Hooks

Short sentences referencing what the company does. Use when the email opens with
a reference to the recipient's company.

#### Website Hook

References what the company does based on their website content. **Always include
`{{linkedin_company_description}}` as a fallback** — when website data is empty, LinkedIn
fills the gap and ensures every contact gets a hook.

**Variables:** `{{company_name}}`, `{{website_text_summary}}`, `{{linkedin_company_description}}`
**Typical output:** `"I saw your company helps retailers optimize their supply chain"`

#### LinkedIn Company Hook

References the company's LinkedIn description — often more focused on mission/positioning.

**Variables:** `{{company_name}}`, `{{linkedin_company_description}}`
**Typical output:** `"I noticed your team is building AI tools for sales teams"`

#### Combined Company Hook

When both website and LinkedIn data are available, uses both for richer context.

**Variables:** `{{company_name}}`, `{{company_website}}`, `{{linkedin_company_description}}`, `{{website_text_summary}}`
**Typical output:** `"I saw that you're helping e-commerce brands scale through automation"`

### B. Person-Based Hooks

Short sentences referencing the person's role, experience, or activity.

#### Experience Hook

References the person's background, current role, or career trajectory.

**Variables:** `{{full_name}}`, `{{position}}`, `{{linkedin_about_me}}`, `{{present_experiences}}`
**Typical output:** `"With your experience leading sales teams at enterprise companies"`

#### LinkedIn Posts Icebreaker

References something the person recently posted about on LinkedIn.

**Variables:** `{{linkedin_latest_posts}}`
**Typical output:** `"I noticed your post about the challenges of scaling outbound"`

#### Education/Skills Hook

References the person's education or specific expertise.

**Variables:** `{{full_name}}`, `{{education_summary}}`, `{{linkedin_skills}}`
**Typical output:** `"With your background in data science and machine learning"`

### C. Language-Specific Columns

Grammar-aware columns for languages with formal address, vocatives, or declension.

#### Gender Title

The gender-appropriate formal title as a **standalone column** — e.g., "pane" / "paní" in Czech,
"Herr" / "Frau" in German, "Panie" / "Pani" in Polish. This is split from the salutation so it
can be combined flexibly with first name vocative or last name vocative in outreach messages.

**Variables:** `{{full_name}}`, `{{position}}`
**Czech example:** `"pane"` / `"paní"`
**German example:** `"Herr"` / `"Frau"`
**Polish example:** `"Panie"` / `"Pani"`

**Usage in outreach messages:**
- Formal: `{{gender_title_-_cz}} {{last_name_vocative_-_cz}}` → "pane Nováku"
- Casual: `{{first_name_vocative_-_cz}}` → "Tomáši"
- Full formal: `Dobrý den, {{gender_title_-_cz}} {{last_name_vocative_-_cz}}` → "Dobrý den, pane Nováku"

#### First Name Vocative

The first name declined into the vocative case (5th grammatical case).

**Variables:** `{{first_name}}`
**Czech example:** `"Tomáši"` from Tomáš, `"Kateřino"` from Kateřina
**Polish example:** `"Tomaszu"` from Tomasz, `"Katarzyno"` from Katarzyna

#### Last Name Vocative

The last name declined into the vocative case — **WITHOUT the gender title prefix**.
The title (pane/paní) is in a separate Gender Title column so they can be combined flexibly.

**Variables:** `{{last_name}}`, `{{full_name}}`, `{{position}}`
**Czech example:** `"Nováku"` (male) / `"Nováková"` (female) — NOT "pane Nováku"
**German example:** `"Schmidt"` / `"Müller"` (unchanged in German)
**Polish example:** `"Kowalski"` / `"Kowalska"` (unchanged in Polish)

---

## Smart Variable Selection

Pick only the variables relevant to the personalization type:

| Personalization | Variables | When to use |
|---|---|---|
| Website hook | `{{company_name}}`, `{{website_text_summary}}`, `{{linkedin_company_description}}` | User wants hook based on company website (LinkedIn as fallback) |
| LinkedIn company hook | `{{company_name}}`, `{{linkedin_company_description}}` | User wants hook from LinkedIn company page |
| Combined company hook | `{{company_name}}`, `{{company_website}}`, `{{linkedin_company_description}}`, `{{website_text_summary}}` | User wants the richest company-based hook |
| Experience hook | `{{full_name}}`, `{{position}}`, `{{linkedin_about_me}}`, `{{present_experiences}}` | User wants hook about the person's background |
| LinkedIn posts icebreaker | `{{linkedin_latest_posts}}` | User wants hook from recent LinkedIn activity |
| Education/skills hook | `{{full_name}}`, `{{education_summary}}`, `{{linkedin_skills}}` | User wants hook about expertise/education |
| Gender title | `{{full_name}}`, `{{position}}` | User wants standalone pane/paní, Herr/Frau, etc. |
| First name vocative | `{{first_name}}` | User wants declined first name |
| Last name vocative | `{{last_name}}`, `{{full_name}}`, `{{position}}` | User wants declined last name (no title prefix) |

---

## Prompt Writing Guidelines for Personalization

### Rules for All Personalization Prompts

1. **Enforce word limit.** Every prompt must include: "Keep your output under 16 words."
   This is the single most important rule — it controls hallucination.

2. **Natural tone.** Output should sound like something a human would write in an email.
   Never salesy, never robotic. Conversational and genuine.

3. **Sentence fragment, not a full sentence.** Hooks are parts of a larger message.
   They don't need to be grammatically complete on their own.

4. **Fallback for missing data.** Always include: "If there is not enough information,
   return empty string."

5. **No output format instructions.** The system prompt handles JSON formatting.
   Never ask for `classification:`, `result:`, or any custom format.

6. **One task per prompt.** Each AI column does one personalization. Don't combine
   a hook + salutation in a single prompt.

7. **Language instruction.** For non-English output, add at the end:
   "Write your output in {language}." This goes AFTER the input variables.

### Rules for Hooks (Company & Person)

- Reference something **specific** from the input — never generic
- Bad: "I see your company is doing great things" (too vague)
- Good: "I saw your company helps SaaS teams reduce churn with AI" (specific)
- Start with natural openers: "I saw...", "I noticed...", "With your...", "Given your..."
- The hook will be followed by a transition phrase the user controls — don't add one
- Focus on business-relevant content — skip personal/vacation/birthday mentions

### Rules for Vocatives and Salutations

- Include explicit declension rules with examples in the prompt
- Include gender detection logic (name endings, position keywords)
- For Czech: masculine names typically end in consonant, feminine in -a/-á/-e
- Provide fallback for ambiguous names: use the more formal/neutral option
- Never use diminutive forms — always formal/standard vocative

---

## Prompt Templates

### Company Website Hook (any language)

**Column name:** `Website Hook` or `Website Hook - {LANG}`
**`is_boolean`: false**

**⚠️ Always include `{{linkedin_company_description}}` alongside `{{website_text_summary}}`.** Some contacts have no website data — LinkedIn fills the gap and ensures every contact gets a hook.

```
Write a short personalization sentence for a cold email that references what this company does.

Rules:
- Keep your output under 16 words
- Start with "I saw" or "I noticed" followed by a specific reference to the company's activity
- Use the most interesting and specific detail from the available data
- Reference a product, service, market, technology, or initiative — be concrete
- Do NOT be generic (no "I see your company is doing great things")
- Do NOT include a call to action or transition phrase
- The tone should be natural and conversational, not salesy
- If there is not enough information, return empty string

Input:
- Company Name: {{company_name}}
- Company Website Summary: {{website_text_summary}}
- LinkedIn Company Description: {{linkedin_company_description}}
```

**For non-English output**, replace the opener with the native-language equivalent and append the language instruction:
- German: "Ich habe gesehen" / "Mir ist aufgefallen" + `Write your output in German.`
- Polish: "Zauważyłem" / "Zauważyłam" + `Write your output in Polish.`
- Czech: "Všiml jsem si" / "Zaujalo mě" + `Write your output in Czech.`
- Other languages: translate the opener naturally + `Write your output in {language}.`

**For non-English output, append before closing:**
```
Write your output in {language}.
```

### Company LinkedIn Hook (any language)

**Column name:** `Company Hook` or `Company Hook - {LANG}`
**`is_boolean`: false**

```
Write a short personalization sentence for a cold email that references this company's focus or mission based on their LinkedIn description.

Rules:
- Keep your output under 16 words
- Start with "I noticed" or "I saw" followed by a specific reference to the company
- Reference their mission, product focus, or market positioning
- Do NOT be generic or vague
- Do NOT include a call to action or transition phrase
- The tone should be natural and conversational, not salesy
- If there is not enough information, return empty string

Input:
- Company Name: {{company_name}}
- LinkedIn Company Description: {{linkedin_company_description}}
```

### Combined Company Hook (any language)

**Column name:** `Company Hook` or `Company Hook - {LANG}`
**`is_boolean`: false**

```
Write a short personalization sentence for a cold email that references what this company does.

Rules:
- Keep your output under 16 words
- Start with "I saw" or "I noticed" followed by a specific reference to the company's activity
- Use the most interesting and specific detail from the available data
- Reference a product, service, market, technology, or initiative — be concrete
- Do NOT be generic (no "I see your company is doing great things")
- Do NOT include a call to action or transition phrase
- The tone should be natural and conversational, not salesy
- If there is not enough information, return empty string

Input:
- Company Name: {{company_name}}
- Company Website: {{company_website}}
- LinkedIn Company Description: {{linkedin_company_description}}
- Company Website Summary: {{website_text_summary}}
```

### Person Experience Hook (any language)

**Column name:** `Experience Hook` or `Experience Hook - {LANG}`
**`is_boolean`: false**

```
Write a short personalization sentence for a cold email that references this person's professional background or current role.

Rules:
- Keep your output under 16 words
- Start with "With your experience" or "Given your background" or similar natural opener
- Reference something specific from their role, expertise, or career focus
- Do NOT mention the person's name in the output
- Do NOT be generic (no "With your impressive background")
- Do NOT include a call to action or transition phrase
- Focus on business-relevant aspects of their experience
- If there is not enough information, return empty string

Input:
- Position: {{position}}
- LinkedIn About Me: {{linkedin_about_me}}
- Present Positions Summary: {{present_experiences}}
```

### LinkedIn Posts Icebreaker (any language)

**Column name:** `Icebreaker` or `Icebreaker - {LANG}`
**`is_boolean`: false**

**IMPORTANT:** This column requires `LinkedIn Latest Posts` (`li_latest_posts`) to be enriched first. Only enrich `li_latest_posts` when the user explicitly requests icebreaker personalization from LinkedIn posts.

**How to detect company posts vs personal posts in the input:**
- **Company posts** start with `"Company post:"` prefix followed by the post content. Example: `"Company post: We're excited to announce our new partnership with..."`
- **Personal posts** start directly with the post content, without any prefix. Example: `"Just published my thoughts on the future of sales automation..."`

```
Write a personalized icebreaker sentence for a cold email based on the person's latest LinkedIn post.

Rules:
- Keep your output under 16 words
- How to detect the post type:
  - If the input starts with "Company post:" → this is a post from the company LinkedIn page, use "I noticed on your company LinkedIn..."
  - If the input does NOT start with "Company post:" → this is the person's own post, use "I noticed on your LinkedIn..."
- Focus on business-related content (product launches, insights, industry opinions)
- Skip personal posts about vacations, birthdays, hobbies — if only personal content exists, return empty string
- The tone should be natural and not salesy
- Do NOT include a call to action or transition phrase
- If the input is empty or has no meaningful business content, return empty string

Input:
- LinkedIn Latest Posts: {{linkedin_latest_posts}}
```

### Education/Skills Hook (any language)

**Column name:** `Skills Hook` or `Skills Hook - {LANG}`
**`is_boolean`: false**

```
Write a short personalization sentence for a cold email that references this person's education or specific expertise.

Rules:
- Keep your output under 16 words
- Start with "With your background in" or "Given your expertise in" or similar natural opener
- Reference a specific field of study, skill, or area of expertise
- Do NOT mention the person's name in the output
- Do NOT be generic
- Do NOT include a call to action or transition phrase
- If there is not enough information, return empty string

Input:
- Education Summary: {{education_summary}}
- LinkedIn Skills: {{linkedin_skills}}
```

---

## Language-Specific Templates

### Czech (CZ) Salutation (Legacy — Combined)

**NOTE:** The preferred approach is to use **3 separate columns** instead of this combined salutation:
1. `Gender Title - CZ` → "pane" / "paní"
2. `CZ First Name Vocative` → "Tomáši" / "Kateřino"
3. `CZ Last Name Vocative` → "Nováku" / "Nováková"

This gives maximum flexibility in outreach messages:
- `Dobrý den, {{gender_title_-_cz}} {{last_name_vocative_-_cz}}` → formal
- `Zdravím, {{first_name_vocative_-_cz}}` → casual follow-up

**Only use the combined salutation below if the user explicitly asks for a single salutation column.**

**Column name:** `CZ Salutation`
**`is_boolean`: false**

```
Generate a formal Czech salutation for a business email.

Your task:
1. Determine the person's gender from their name and job title
2. Create the correct formal greeting in Czech

Gender detection rules:
- Feminine indicators: first name ends in -a, -e, or -ie (Jana, Marie, Kateřina, Lucie); last name ends in -ová, -á (Nováková, Černá)
- Masculine indicators: first name ends in a consonant or -o (Jan, Tomáš, Michal, Marek); last name without -ová/-á suffix
- Position can help: titles like "ředitelka", "manažerka", "náměstkyně" indicate female; "ředitel", "manažer", "náměstek" indicate male
- If ambiguous, default to masculine form

Czech salutation rules:
- Masculine: "Dobrý den, pane" + last name in vocative case
  - Last name vocative: -ák → -áku (Novák → Nováku, Dvořák → Dvořáku)
  - -ek → -ku (Voříšek → Voříšku, Havlíček → Havlíčku)
  - -ec → -če (Němec → Němče)
  - -ský/-cký → -ský/-cký (unchanged: Novotný → Novotný)
  - consonant (general) → add -e (Vlach → Vlache, Procházka → Procházko)
  - -ka → -ko (Procházka → Procházko, Růžička → Růžičko)
  - -da → -do (Svoboda → Svobodo)
  - -ta → -to (Vávrta → Vávrto)
- Feminine: "Dobrý den, paní" + last name in nominative (unchanged)
  - Nováková stays Nováková
  - Dvořáková stays Dvořáková

Return only the salutation, nothing else.
Examples: "Dobrý den, pane Nováku", "Dobrý den, paní Dvořáková", "Dobrý den, pane Blaťáku"

If the name is not recognizable or empty, return empty string.

Input:
- Full Name: {{full_name}}
- Position: {{position}}
```

### Czech (CZ) First Name Vocative

**Column name:** `CZ First Name Vocative`
**`is_boolean`: false**

```
You are an expert in Czech grammar, specifically declension rules for the vocative case (5. pád).

Given a Czech first name:
1. Add any missing diacritics (háčky and čárky)
2. Transform the name into the correct vocative form

Masculine vocative rules:
- Names ending in a hard consonant: add -e (Tomáš → Tomáši is an exception because of š)
- -áš → -áši (Tomáš → Tomáši, Lukáš → Lukáši)
- -eš → -eši (Matěj... but: Aleš → Aleši)
- -an → -ane (Jan → Jane, Štěpán → Štěpáne)
- -el → -ele or -li (Michal → Michale, Pavel → Pavle)
- -ek → -ku (Marek → Marku, Zdeněk → Zdeňku, Vojtěch... but: Leoš → Leoši)
- -il → -ile (Emil → Emile)
- -in → -ine (Martin → Martine)
- -ír → -íře (Vladimír → Vladimíre)
- -ej → -eji (Ondřej → Ondřeji, Matěj → Matěji)
- -ec → -če (Otec exception, but for names: rarely applies)
- -tr → -tře (Petr → Petře)
- -ip → -ipe (Filip → Filipe)
- -ub → -ube (Jakub → Jakube)
- -id → -ide (David → Davide)
- -os → -osi (Miloš → Miloši)
- -áv → -áve (Václav → Václave)
- -ek → -ku (Radek → Radku)
- -o ending: -o (Ivo → Ivo, stays the same)
- -a ending (masculine): -o (Nikola → Nikolo)

Feminine vocative rules:
- -a → -o (Jana → Jano, Petra → Petro, Simona → Simono, Kateřina → Kateřino)
- -ie/-e → stays the same (Marie → Marie, Lucie → Lucie, Adéle → Adéle)
- -ka → -ko (Lenka → Lenko, Zuzanka → Zuzanko — but for formal usage, avoid diminutives)

IMPORTANT: Use only the standard (official) vocative form, never diminutives or familiar forms.
- "Marie" → "Marie" (NOT "Maruško")
- "Simona" → "Simono" (NOT "Simonko")
- "Kateřina" → "Kateřino" (NOT "Katko")

Return only the vocative form, nothing else. If no name is provided, return empty string.

Input:
- First Name: {{first_name}}
```

### Czech (CZ) Gender Title

**Column name:** `Gender Title - CZ`
**`is_boolean`: false**

```
Determine the correct Czech gender-based title for this person.

Rules:
- If the person is male, return "pane"
- If the person is female, return "paní"
- Determine gender from the full name and position
- Czech female names: first name typically ends in -a, -e, -ie (Jana, Marie, Kateřina, Lucie); last name ends in -ová, -á (Nováková, Černá)
- Czech male names: first name typically ends in consonant or -o (Jan, Tomáš, Michal, Marek); last name without -ová/-á suffix
- Position can help: titles like "ředitelka", "manažerka", "náměstkyně" indicate female; "ředitel", "manažer", "náměstek" indicate male
- If ambiguous, default to "pane"
- Return ONLY "pane" or "paní", nothing else.

Input:
- Full Name: {{full_name}}
- Position: {{position}}
```

### Czech (CZ) Last Name Vocative

**Column name:** `CZ Last Name Vocative`
**`is_boolean`: false**

**IMPORTANT:** This column outputs ONLY the declined last name — no title prefix.
The title (pane/paní) is in the separate "Gender Title - CZ" column.

```
You are an expert in Czech grammar. Generate the vocative form (5. pád) of a Czech last name.

Your task:
1. Determine the person's gender from their full name and position
2. Apply the correct vocative declension to the last name
3. Return ONLY the declined last name — do NOT include "pane" or "paní"

Gender detection:
- Feminine: first name ends in -a/-e/-ie (Jana, Marie, Lucie); last name ends in -ová/-á (Nováková)
- Masculine: first name ends in consonant/-o (Jan, Tomáš, Michal); last name without -ová
- Position keywords: -ka/-kyně suffix = female (manažerka, ředitelka), no suffix = male (manažer, ředitel)

Masculine last name vocative rules:
- -ák → -áku (Novák → Nováku, Dvořák → Dvořáku, Blaťák → Blaťáku, Polák → Poláku)
- -ek → -ku (Havlíček → Havlíčku, Voříšek → Voříšku)
- -ec → -če (Němec → Němče, Kopec → Kopče)
- -ík → -íku (Sedlačík → Sedlačíku)
- -ka → -ko (Procházka → Procházko, Růžička → Růžičko, Kafka → Kafko)
- -da → -do (Svoboda → Svobodo)
- -ý/-í → unchanged (Novotný → Novotný, Malý → Malý)
- general consonant ending → add -e (Vlach → Vlache)

Feminine last name rules:
- Keep the last name unchanged (nominative = vocative for feminine)
- Nováková → Nováková, Dvořáková → Dvořáková

Return ONLY the declined last name (e.g., "Nováku", "Dvořáková", "Blaťáku"), nothing else.
Do NOT include "pane" or "paní" — that is handled by a separate column.
If the name is not recognizable or empty, return empty string.

Input:
- Last Name: {{last_name}}
- Full Name: {{full_name}}
- Position: {{position}}
```

### Polish (PL) Salutation

**Column name:** `PL Salutation`
**`is_boolean`: false**

```
Generate a formal Polish salutation for a business email.

Your task:
1. Determine the person's gender from their first name and last name
2. Create the correct formal greeting in Polish

Gender detection rules:
- Feminine indicators: first name ends in -a (Anna, Katarzyna, Monika, Agnieszka, Magdalena, Joanna, Ewa, Dorota, Aleksandra, Natalia, Sonia); last name ends in -ska, -cka, -dzka, -wska (Kowalska, Nowacka)
- Masculine indicators: first name ends in a consonant or -o (Jan, Tomasz, Michał, Marek, Piotr, Krzysztof, Andrzej, Adam, Carlos, John, Sean); last name ends in -ski, -cki, -dzki, -wski or consonant (Kowalski, Nowak)
- If ambiguous, default to masculine form

Polish salutation format:
- Male: "Szanowny Panie" + last name in nominative (unchanged)
  - Kowalski → "Szanowny Panie Kowalski"
  - Nowak → "Szanowny Panie Nowak"
- Female: "Szanowna Pani" + last name in nominative (unchanged)
  - Kowalska → "Szanowna Pani Kowalska"
  - Nowak → "Szanowna Pani Nowak"

Extract the last name from the full name (last word in the name).

Return only the salutation, nothing else.
Examples: "Szanowny Panie Kowalski", "Szanowna Pani Nowak"

If the name is not recognizable or empty, return empty string.

Input:
- Full Name: {{full_name}}
- Position: {{position}}
```

### German (DE) Salutation

**Column name:** `DE Salutation`
**`is_boolean`: false**

```
Generate a formal German salutation for a business email.

Your task:
1. Determine the person's gender from their first name
2. Create the correct formal greeting in German

Gender detection rules:
- Common male first names: Hans, Peter, Thomas, Michael, Stefan, Andreas, Martin, Carlos, John, Sean, Marco, Alexander, David, Daniel, Christian, Markus, Frank, Klaus, Jürgen, Wolfgang, Bernd, Ralf, Uwe, Dirk, Oliver, Patrick, Sven, Tobias, Florian, Matthias, Christoph
- Common female first names: Anna, Maria, Marie, Claudia, Sabine, Petra, Monika, Susanne, Andrea, Karin, Julia, Sandra, Nicole, Katharina, Stefanie, Birgit, Heike, Martina, Simone, Christina, Sonia, Laura, Lisa, Sarah, Elena, Nadine, Anja, Tanja, Silke, Melanie
- Names ending in -a, -e, -ie, -ine are typically female
- Names ending in consonant are typically male
- If ambiguous, use "Sehr geehrte/r" as neutral form

German salutation format:
- Male: "Sehr geehrter Herr {last_name}"
- Female: "Sehr geehrte Frau {last_name}"
- Last name stays unchanged (no declension in German)

Extract the last name from the full name (last word in the name).

Return only the salutation, nothing else.
Examples: "Sehr geehrter Herr Schmidt", "Sehr geehrte Frau Müller"

If the name is not recognizable or empty, return empty string.

Input:
- Full Name: {{full_name}}
- Position: {{position}}
```

### Generic Salutation Template (any language)

When a user requests a salutation in a language not listed above, use this template
and fill in the language-specific rules:

**Column name:** `{LANG} Salutation`
**`is_boolean`: false**

```
Generate a formal {language} salutation for a business email.

Your task:
1. Determine the person's gender from their name and job title
2. Create the correct formal greeting in {language}

{LANGUAGE_SPECIFIC_GENDER_RULES}

{LANGUAGE_SPECIFIC_SALUTATION_FORMAT}

Return only the salutation, nothing else.

If the name is not recognizable or empty, return empty string.

Input:
- Full Name: {{full_name}}
- Position: {{position}}
```

**Language-specific rules to fill in:**

**German:**
- Gender: from first name (Hans = male, Anna = female) and title (Geschäftsführerin = female)
- Format: "Sehr geehrter Herr {last_name}" / "Sehr geehrte Frau {last_name}"
- No declension needed — last names stay in nominative

**Polish:**
- Gender: first names ending in -a are typically female; last names ending in -ska/-cka are female
- Format: "Szanowny Panie {last_name_vocative}" / "Szanowna Pani {last_name}"
- Masculine vocative: -ski → -ski (unchanged), -cki → -cki, -ek → -ku, -ak → -aku
- Feminine: last name stays unchanged

**French:**
- Gender: from first name (Jean = male, Marie = female)
- Format: "Cher Monsieur {last_name}" / "Chère Madame {last_name}"
- No declension needed

**Spanish:**
- Format: "Estimado Sr. {last_name}" / "Estimada Sra. {last_name}"
- No declension needed

---

## Multi-Language System

### How Language Selection Works

1. **User specifies the language** in their request: "website hook in German", "Czech salutation",
   "icebreaker in Polish"
2. **Default is English** — if no language specified, output is in English
3. **For hooks**: append `"Write your output in {language}."` at the end of the prompt
4. **For vocatives/salutations**: use the language-specific template with built-in grammar rules

### Language Capabilities

| Language | Hooks | Salutation | First Name Vocative | Last Name Vocative |
|----------|-------|------------|--------------------|--------------------|
| English | ✅ | N/A (no formal address convention) | N/A | N/A |
| Czech | ✅ | ✅ (Dobrý den, pane/paní) | ✅ (5. pád) | ✅ (5. pád) |
| Polish | ✅ | ✅ (Szanowny Panie/Pani) | ✅ (wołacz) | ✅ (wołacz) |
| Slovak | ✅ | ✅ (Dobrý deň, pán/pani) | ✅ (5. pád) | ✅ (5. pád) |
| German | ✅ | ✅ (Sehr geehrter Herr/Frau) | N/A | N/A |
| French | ✅ | ✅ (Cher Monsieur/Madame) | N/A | N/A |
| Spanish | ✅ | ✅ (Estimado Sr./Sra.) | N/A | N/A |
| Any other | ✅ | Ask user for format | Ask user for rules | Ask user for rules |

### Auto-Generating Salutation with Hooks

**IMPORTANT: Whenever a user requests any hook or personalization in a specific language,
ALWAYS auto-generate the salutation column for that language too.** The salutation is a
fundamental part of any outreach — the user should never have to ask for it separately.

**Automatic behavior when user requests a hook in any language:**
1. Generate the requested hook column (e.g., `Website Hook - DE`)
2. **Automatically also generate** the salutation column (e.g., `DE Salutation`)
3. Preview both together so the user sees the full opening of their email

**For languages with vocatives (Czech, Polish, Slovak) — also auto-generate:**
- `Gender Title - {LANG}` — standalone title ("pane"/"paní", "Panie"/"Pani")
- `{LANG} First Name Vocative` — declined first name
- `{LANG} Last Name Vocative` — declined last name (WITHOUT title prefix)

**For languages without vocatives (German, French, Spanish) — auto-generate:**
- `Gender Title - {LANG}` — standalone title ("Herr"/"Frau", "Monsieur"/"Madame", "Sr."/"Sra.")

The user can opt out of auto-generating salutations by saying "just the hook" or "no salutation".

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
  "is_boolean": false
}
```

Note: All personalization prompts use `is_boolean: false` (string mode).

### Preview — Fetch Results

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/?column_name={column_name}&is_boolean=false
```

Returns: `[{"person": "Name", "result": "value"}, ...]`

### Fetch Contact Data (for preview context)

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/people?page=1&page_size=5
```

Returns: `{"items": [...], "count": N}` where each item has `contact_data` with
`full_name`, `position`, `linkedin`, `company_linkedin`, `company_website`, `company_name`, etc.

### Launch Full Personalization

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
```

```json
{
  "magic_column_type": "ai_custom_column",
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": false
}
```

> In the `prompt` field, escape all newlines as `\n` (JSON string).
> Template variables like `{{company_name}}` are filled by Leadspicker automatically.

### cURL Example — Website Hook

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "ai_custom_column",
    "column_name": "Website Hook",
    "prompt": "Write a short personalization sentence for a cold email that references what this company does based on their website.\n\nRules:\n- Keep your output under 16 words\n- Start with \"I saw\" or \"I noticed\" followed by a specific reference to the company'\''s activity\n- Reference something concrete — a product, service, market, or initiative\n- Do NOT be generic (no \"I see your company is doing great things\")\n- Do NOT include a call to action or transition phrase\n- The tone should be natural and conversational, not salesy\n- If there is not enough information, return empty string\n\nInput:\n- Company Name: {{company_name}}\n- Company Website Summary: {{website_text_summary}}",
    "is_boolean": false
  }'
```

### cURL Example — CZ Salutation

```bash
curl -X POST "https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns" \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-api-key: {api_key}' \
  -d '{
    "magic_column_type": "ai_custom_column",
    "column_name": "CZ Salutation",
    "prompt": "Generate a formal Czech salutation for a business email.\n\nYour task:\n1. Determine the person'\''s gender from their name and job title\n2. Create the correct formal greeting in Czech\n\nGender detection rules:\n- Feminine indicators: first name ends in -a, -e, or -ie (Jana, Marie, Kateřina, Lucie); last name ends in -ová, -á (Nováková, Černá)\n- Masculine indicators: first name ends in a consonant or -o (Jan, Tomáš, Michal, Marek); last name without -ová/-á suffix\n- Position can help: titles like \"ředitelka\", \"manažerka\", \"náměstkyně\" indicate female; \"ředitel\", \"manažer\", \"náměstek\" indicate male\n- If ambiguous, default to masculine form\n\nCzech salutation rules:\n- Masculine: \"Dobrý den, pane\" + last name in vocative case\n  - -ák → -áku (Novák → Nováku, Dvořák → Dvořáku)\n  - -ek → -ku (Voříšek → Voříšku, Havlíček → Havlíčku)\n  - -ec → -če (Němec → Němče)\n  - -ka → -ko (Procházka → Procházko, Růžička → Růžičko)\n  - -da → -do (Svoboda → Svobodo)\n  - -ý/-í → unchanged (Novotný → Novotný)\n  - general consonant → add -e (Vlach → Vlache)\n- Feminine: \"Dobrý den, paní\" + last name unchanged (Nováková → Nováková)\n\nReturn only the salutation, nothing else.\nExamples: \"Dobrý den, pane Nováku\", \"Dobrý den, paní Dvořáková\", \"Dobrý den, pane Blaťáku\"\n\nIf the name is not recognizable or empty, return empty string.\n\nInput:\n- Full Name: {{full_name}}\n- Position: {{position}}",
    "is_boolean": false
  }'
```

---

## Workflow Step by Step

### Step 1: Collect Input

Gather `project_id`, `api_key`, personalization request, and target language.
If the user doesn't provide a `column_name`, generate one from the type + language.

### Step 2: Determine Personalization Type

Based on the user's request, decide:

1. **What type?** → Company hook, Person hook, Icebreaker, Salutation, or Vocative
2. **Which variables?** → Select from the Smart Variable Selection table
3. **Which language?** → Default English, or user-specified language
4. **Auto-include salutation**: If the user requests any hook in a non-English language,
   automatically also prepare the salutation column for that language (see Auto-Generating
   Salutation with Hooks section). For vocative languages, also include vocative columns.

### Step 3: Write the Prompt

Build the prompt following the guidelines:
1. Clear task definition
2. Word limit rule (≤14 words for hooks)
3. Specific rules for tone, style, and content
4. Fallback for missing data
5. Input variables (only the relevant ones)
6. Language instruction if non-English

### Step 4: Show Prompt to User

Before calling the API, show:
- The column name
- The full prompt text
- The target language

Ask for approval before proceeding.

### Step 5: Preview — Test on First 5 Rows

**Always run a preview before launching.** This lets the user verify the personalization
works correctly before applying it to all contacts.

#### 5a. Submit the preview request

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/
```

Body:
```json
{
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": false
}
```

#### 5b. Fetch contact data for context

```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/people?page=1&page_size=5
```

#### 5c. Fetch preview results

Wait a few seconds, then:
```
GET https://app.leadspicker.com/app/sb/api/projects/{project_id}/ai-prompt-preview/?column_name={column_name}&is_boolean=false
```

#### 5d. Present combined preview

Show a table combining contact data with personalization output:

```
Preview Results (first 5 rows):

| Name | Position | Company | Result |
|------|----------|---------|--------|
| Tomáš Blaťák | Sales Manager | Leadspicker | Dobrý den, pane Blaťáku |
| Jana Nováková | CEO | Acme s.r.o. | Dobrý den, paní Nováková |
...

Does this look correct? Should I launch for all contacts?
```

#### 5e. Wait for user approval

- If approved → proceed to Step 6
- If changes needed → go back to Step 3
- If cancel → stop

### Step 6: Launch Full Personalization

```
POST https://app.leadspicker.com/app/sb/api/projects/{project_id}/magic-columns
```

```json
{
  "magic_column_type": "ai_custom_column",
  "column_name": "{column_name}",
  "prompt": "{prompt_text_with_escaped_newlines}",
  "is_boolean": false
}
```

### Step 7: Report and Suggest Next Steps

After successful creation:
- Confirm the column was created
- Suggest related personalizations:
  - After website hook → "Want a LinkedIn company hook too?"
  - After icebreaker → "Want a hook based on their experience?"
  - After salutation → "Want first name and last name vocatives too?"
  - After CZ columns → "Want hooks in Czech as well?"

---

## Batch Mode — Personalization Pipeline

When the user asks for "full personalization" or "all hooks":

### English Personalization Package

```
Column 1: Website Hook
Column 2: Company Hook (LinkedIn)
Column 3: Experience Hook
Column 4: Icebreaker (LinkedIn Posts)
```

### Czech Personalization Package

```
Column 1: Website Hook - CZ
Column 2: Company Hook - CZ
Column 3: Experience Hook - CZ
Column 4: Icebreaker - CZ
Column 5: Gender Title - CZ (pane/paní)
Column 6: CZ First Name Vocative
Column 7: CZ Last Name Vocative (no title prefix)
```

### Any Language Package (with vocatives — CZ/PL/SK)

```
Column 1: Website Hook - {LANG}
Column 2: Company Hook - {LANG}
Column 3: Experience Hook - {LANG}
Column 4: Icebreaker - {LANG}
Column 5: Gender Title - {LANG} (standalone title)
Column 6: {LANG} First Name Vocative
Column 7: {LANG} Last Name Vocative (no title prefix)
```

### Any Language Package (without vocatives — DE/FR/ES)

```
Column 1: Website Hook - {LANG}
Column 2: Company Hook - {LANG}
Column 3: Experience Hook - {LANG}
Column 4: Icebreaker - {LANG}
Column 5: Gender Title - {LANG} (Herr/Frau, Monsieur/Madame, Sr./Sra.)
```

Execute all columns sequentially with 1-second delay between API calls.
Preview the first column to verify quality, then launch all after approval.

---

## Natural Language → Personalization Matching

| User says... | Personalization type | Variables |
|---|---|---|
| "website hook", "hook z webu", "opening from website" | Website Hook | Company |
| "company hook", "hook o firmě", "what the company does" | Company LinkedIn Hook | Company |
| "experience hook", "hook o zkušenostech" | Experience Hook | Person Detailed |
| "icebreaker", "opener from posts", "hook z příspěvků" | LinkedIn Posts Icebreaker | Posts |
| "skills hook", "hook o dovednostech" | Education/Skills Hook | Education + Skills |
| "salutation", "greeting", "oslovení", "pozdrav" | Salutation | Name + Position |
| "vocative", "vokativ", "5. pád" | Vocative (first or last name) | Name |
| "first name vocative", "křestní jméno vokativ" | First Name Vocative | First Name |
| "last name vocative", "příjmení vokativ" | Last Name Vocative | Last Name + Position |
| "full personalization", "celá personalizace" | Batch Pipeline | All relevant |
| "Czech greeting", "české oslovení" | CZ Salutation | Name + Position |
| "German greeting", "German salutation" | DE Salutation | Name + Position |
| "personalize in Czech", "personalizace česky" | Czech Package | All |
| "hook in German", "hook auf Deutsch" | Hook in German | Company or Person |

---

## Error Handling

| HTTP Status | Likely Cause | Resolution |
|-------------|-------------|------------|
| `401 Unauthorized` | Bad or expired API key | Verify `x-api-key` with user |
| `404 Not Found` | Wrong `project_id` | Verify project ID |
| `400 Bad Request` | Malformed body or invalid type | Check JSON formatting |
| `422 Unprocessable` | Column name already exists | Use a different column name |
| `429 Too Many Requests` | Rate limit on batch | Increase delay between calls to 2-3s |

---

## Security

- **Never log or display** the full API key — confirm only the last 6 characters
- Use the API key only for Leadspicker API calls, never send it elsewhere
- Before calling the API, **always show the prompt to the user** for approval
- Write all prompts in English for best GPT-5.4-Mini performance (add language output instruction at the end)
