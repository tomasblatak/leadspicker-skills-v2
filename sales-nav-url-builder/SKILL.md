---
name: sales-nav-url-builder
description: >
  Builds LinkedIn Sales Navigator search URLs programmatically from natural language filter
  descriptions. Use this skill whenever the user wants to create, build, generate, or modify a
  Sales Navigator search URL — for example when setting up a Leadspicker robot that needs a
  Sales Nav URL as input, when they describe a target audience and need the search link, or when
  they paste an existing Sales Nav URL and want to add or remove filters. Also triggers when the
  user mentions Sales Navigator filters (companies, job titles, seniority, function, geography),
  asks to "find people on LinkedIn" with specific criteria, wants to parse or decode a Sales Nav
  URL, or needs to export a company list from a Sales Nav link. Triggers on: "sales navigator
  URL", "sales nav link", "build search URL", "LinkedIn people search URL", "salesnav filter",
  "find people at [company]", "create a search for [title] at [company]", "parse this sales nav
  URL", "add companies to sales nav search", "sales nav robot URL", any mention of building
  a LinkedIn search link with filters.
---

# Sales Navigator URL Builder

Builds valid LinkedIn Sales Navigator people search URLs from filter descriptions using the
bundled `scripts/sales_nav_url_builder.py` utility. The generated URLs can be opened directly
in a browser or used as input for Leadspicker `salesnav_monitor` robots.

## When to use this skill

- User describes an audience and needs a Sales Nav search URL
- User wants to set up a Leadspicker robot and needs the search URL first
- User pastes a Sales Nav URL and wants to modify it (add/remove companies, filters)
- User wants to parse a Sales Nav URL to see what filters it contains
- User wants to export a company list from a Sales Nav URL to CSV

## How the utility works

The script at `scripts/sales_nav_url_builder.py` contains a `SalesNavSearch` class with all
reference data hardcoded (seniority IDs, function IDs, geo URN IDs, industry codes). You
generate the URL by writing a short Python script that uses this class, then running it.

## Workflow

### Step 1: Understand the filters

Extract from the user's request which filters they want. The available filters are:

| Filter | Method | Accepts |
|--------|--------|---------|
| Companies | `add_companies()` | List of names, or dict of `{name: org_id}` |
| Job titles | `add_titles()` | List of title strings (free text) |
| Seniority | `add_seniority()` | Names: "Director", "VP", "CXO", "Manager", "Owner", "Partner" |
| Function | `add_functions()` | Names: see complete list below |
| Region | `add_regions()` | Country/city names: "Germany", "Netherlands", "France", "UK", etc. |
| Industry | `add_industries()` | Names: "Logistics and Supply Chain", "Retail", "Automotive", etc. |
| Company size | `add_company_headcount()` | Codes: "A" through "I" (see reference below) |
| Keywords | `set_keywords()` | Boolean search: `logistics AND "supply chain"` |
| Changed jobs | `set_changed_jobs(True)` | People who changed jobs in last 90 days |
| Posted on LinkedIn | `set_posted_on_linkedin(True)` | People who posted in last 30 days |

If the user's request is clear, proceed directly. If ambiguous, ask one focused question
covering all missing filters at once — don't ask one by one.

### Step 2: Write and run the Python script

Write an inline Python script that imports from the bundled utility and builds the URL.
The script path is relative to THIS skill's directory: `scripts/sales_nav_url_builder.py`.

**Building a new URL:**
```python
import sys
sys.path.insert(0, "<absolute-path-to-this-skill>/scripts")
from sales_nav_url_builder import SalesNavSearch

search = SalesNavSearch()
search.add_companies(["BMW", "Siemens"])
search.add_titles(["VP of Logistics", "Head of Supply Chain"])
search.add_seniority(["Director", "VP", "CXO"])
search.add_functions(["Operations", "Purchasing"])
search.add_regions(["Germany", "Netherlands"])
search.set_changed_jobs(True)
url = search.build_url()
print(url)
```

**Parsing an existing URL:**
```python
import sys
sys.path.insert(0, "<absolute-path-to-this-skill>/scripts")
from sales_nav_url_builder import SalesNavSearch

search = SalesNavSearch.from_url("https://www.linkedin.com/sales/search/people?query=...")
print(search.summary())
```

**Modifying an existing URL (add/remove filters):**
```python
import sys
sys.path.insert(0, "<absolute-path-to-this-skill>/scripts")
from sales_nav_url_builder import SalesNavSearch

search = SalesNavSearch.from_url("<existing_url>")
search.add_companies(["FedEx", "Royal Mail"])
search.remove_companies(["Netto"])
search.add_seniority(["VP", "CXO"])
url = search.build_url()
print(url)
```

### Step 3: Present the result

Show the user:
1. A summary of the filters applied (use `search.summary()`)
2. The generated URL
3. If relevant, mention that this URL can be used as input for a Leadspicker `salesnav_monitor` robot

### Working with company org IDs

Companies can be added two ways:

- **Text-only** (simpler, fuzzy matching): `search.add_companies(["BMW", "Siemens"])`
- **With org ID** (exact matching): `search.add_companies({"Leadspicker": "urn:li:organization:11169328"})`

If the user provides a LinkedIn company URL like `linkedin.com/company/leadspicker/`, you
won't be able to resolve the org ID automatically. Use text-only matching, or if the user
has the org ID from a previous Sales Nav URL, use that.

## Complete Reference Data

### Seniority Levels (ID -> Name)
| ID | Level |
|----|-------|
| 3 | Entry |
| 4 | Senior |
| 5 | Manager |
| 6 | Director |
| 7 | VP |
| 8 | CXO |
| 9 | Partner |
| 10 | Owner |

### Functions (ID -> Name) — all 26
| ID | Function |
|----|----------|
| 1 | Accounting |
| 2 | Administrative |
| 3 | Arts and Design |
| 4 | Business Development |
| 5 | Community and Social Services |
| 6 | Consulting |
| 7 | Education |
| 8 | Engineering |
| 9 | Entrepreneurship |
| 10 | Finance |
| 11 | Healthcare Services |
| 12 | Human Resources |
| 13 | Information Technology |
| 14 | Legal |
| 15 | Marketing |
| 16 | Media and Communication |
| 17 | Military and Protective Services |
| 18 | Operations |
| 19 | Product Management |
| 20 | Program and Project Management |
| 21 | Purchasing |
| 22 | Quality Assurance |
| 23 | Real Estate |
| 24 | Research |
| 25 | Sales |
| 26 | Customer Success and Support |

**Common aliases:** "Supply Chain" and "Logistics" -> Operations (18), "HR" -> 12, "IT" -> 13,
"QA" -> 22, "PM" -> Product Management (19)

### Geography — European Countries (Name -> Geo URN ID)
| Country | Geo URN ID |
|---------|------------|
| Germany | 101282230 |
| Netherlands | 102890719 |
| France | 105015875 |
| United Kingdom | 101165590 |
| Belgium | 100565514 |
| Spain | 105646813 |
| Italy | 103350119 |
| Switzerland | 106693272 |
| Sweden | 105117694 |
| Poland | 105072130 |
| Austria | 103883259 |
| Czech Republic | 104508036 |
| Denmark | 104514075 |
| Norway | 103819153 |
| Finland | 100456013 |
| Portugal | 100364837 |
| Ireland | 104738515 |
| Romania | 106670623 |
| Hungary | 100288700 |

Also supports major cities: London, Paris, Berlin, Amsterdam, Munich, Madrid, Barcelona,
Milan, Brussels, Vienna, Prague, Warsaw, Stockholm, Copenhagen, Dublin, Lisbon, Zurich.

And US locations: USA (103644278), New York, San Francisco, Los Angeles, Chicago.

### Company Headcount
| Code | Size |
|------|------|
| A | Self-employed |
| B | 1-10 |
| C | 11-50 |
| D | 51-200 |
| E | 201-500 |
| F | 501-1,000 |
| G | 1,001-5,000 |
| H | 5,001-10,000 |
| I | 10,001+ |

### Industry Codes (commonly used)
| ID | Industry |
|----|----------|
| 116 | Logistics and Supply Chain |
| 92 | Transportation/Trucking/Railroad |
| 93 | Warehousing |
| 87 | Package/Freight Delivery |
| 27 | Retail |
| 53 | Automotive |
| 55 | Machinery |
| 48 | Construction |
| 25 | Manufacturing |
| 26 | Consumer Goods |
| 4 | Computer Software |
| 6 | Information Technology and Services |
| 43 | Financial Services |

### Keywords with Boolean Search
The `set_keywords()` method supports boolean operators (must be UPPERCASE):
- `AND` — both terms required
- `OR` — either term
- `NOT` — exclude term
- `"quoted phrases"` — exact match
- `(parentheses)` — grouping

Example: `search.set_keywords('logistics AND (warehouse OR "supply chain") NOT retail')`

### Excluding filters
Any filter supports exclusion via `selection_type="EXCLUDED"`:
```python
search.add_companies(["Bad Corp"], selection_type="EXCLUDED")
search.add_titles(["Intern"], filter_type="CURRENT_TITLE", selection_type="EXCLUDED")
```

## URL length caveat

Sales Navigator URLs with many companies (50+) can hit browser URL length limits (~8000 chars).
If the company list is very large, warn the user and suggest using Leadspicker Account Lists
instead — add companies to an Account List in Sales Nav, then filter by that single list.
