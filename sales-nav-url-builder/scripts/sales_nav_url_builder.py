#!/usr/bin/env python3
"""
LinkedIn Sales Navigator URL Builder & Parser

Programmatically build, parse, and modify Sales Navigator search URLs
without using the Sales Navigator UI.

Usage:
    from sales_nav_url_builder import SalesNavSearch

    # Parse existing URL
    search = SalesNavSearch.from_url(existing_url)

    # Build from scratch
    search = SalesNavSearch()
    search.add_companies(["BMW", "Siemens"])
    search.add_titles(["VP of Logistics", "Head of Supply Chain"])
    search.add_seniority(["Director", "VP", "CxO"])
    search.add_regions(["Germany", "Netherlands"])
    search.add_functions(["Operations", "Purchasing"])
    search.set_changed_jobs(True)
    search.set_keywords('logistics AND warehouse')
    url = search.build_url()
"""

import re
import csv
import sys
import json
from urllib.parse import quote, unquote
from io import StringIO


# =============================================================================
# Reference Data
# =============================================================================

SENIORITY_LEVELS = {
    1: "Unpaid", 2: "Training", 3: "Entry", 4: "Senior",
    5: "Manager", 6: "Director", 7: "VP", 8: "CXO",
    9: "Partner", 10: "Owner",
}
SENIORITY_BY_NAME = {v.lower(): k for k, v in SENIORITY_LEVELS.items()}
SENIORITY_BY_NAME.update({
    "cxo": 8, "c-suite": 8, "c-level": 8, "chief": 8,
    "vice president": 7, "vp": 7,
    "director": 6, "manager": 5, "senior": 4,
    "entry": 3, "entry-level": 3, "training": 2, "owner": 10, "partner": 9,
})

FUNCTIONS = {
    1: "Accounting", 2: "Administrative", 3: "Arts and Design",
    4: "Business Development", 5: "Community and Social Services",
    6: "Consulting", 7: "Education", 8: "Engineering",
    9: "Entrepreneurship", 10: "Finance", 11: "Healthcare Services",
    12: "Human Resources", 13: "Information Technology", 14: "Legal",
    15: "Marketing", 16: "Media and Communication",
    17: "Military and Protective Services", 18: "Operations",
    19: "Product Management", 20: "Program and Project Management",
    21: "Purchasing", 22: "Quality Assurance", 23: "Real Estate",
    24: "Research", 25: "Sales", 26: "Customer Success and Support",
}
FUNCTIONS_BY_NAME = {v.lower(): k for k, v in FUNCTIONS.items()}
# Common aliases
FUNCTIONS_BY_NAME.update({
    "hr": 12, "it": 13, "biz dev": 4, "bizdev": 4,
    "ops": 18, "supply chain": 18, "logistics": 18,
    "qa": 22, "pm": 19, "product": 19, "project management": 20,
    "customer support": 26, "customer success": 26, "support": 26,
    "arts": 3, "design": 3, "media": 16, "communication": 16,
})

COMPANY_HEADCOUNT = {
    "A": "Self-employed", "B": "1-10", "C": "11-50", "D": "51-200",
    "E": "201-500", "F": "501-1,000", "G": "1,001-5,000",
    "H": "5,001-10,000", "I": "10,001+",
}

COMPANY_TYPE = {
    "C": "Public Company", "O": "Privately Held", "N": "Non-Profit",
    "G": "Government Agency", "D": "Educational Institution",
    "S": "Self-Employed", "P": "Partnership",
}

# Key European Geo URN IDs
GEO_URNS = {
    # Regions
    "emea": 91000007,
    "europe": 91000000,
    # Countries
    "germany": 101282230, "deutschland": 101282230, "de": 101282230,
    "netherlands": 102890719, "nederland": 102890719, "nl": 102890719,
    "france": 105015875, "fr": 105015875,
    "united kingdom": 101165590, "uk": 101165590, "gb": 101165590,
    "england": 102299470,
    "belgium": 100565514, "be": 100565514,
    "spain": 105646813, "es": 105646813,
    "italy": 103350119, "it_geo": 103350119,
    "switzerland": 106693272, "ch": 106693272,
    "sweden": 105117694, "se": 105117694,
    "poland": 105072130, "pl": 105072130,
    "austria": 103883259, "at": 103883259,
    "czech republic": 104508036, "czechia": 104508036, "cz": 104508036,
    "denmark": 104514075, "dk": 104514075,
    "norway": 103819153, "no": 103819153,
    "finland": 100456013, "fi": 100456013,
    "portugal": 100364837, "pt": 100364837,
    "ireland": 104738515, "ie": 104738515,
    "romania": 106670623, "ro": 106670623,
    "hungary": 100288700, "hu": 100288700,
    "greece": 104677530, "gr": 104677530,
    "slovakia": 103061721, "sk": 103061721,
    "croatia": 104688944, "hr_geo": 104688944,
    "bulgaria": 105333783, "bg": 105333783,
    "slovenia": 106137034, "si": 106137034,
    "luxembourg": 104042105, "lu": 104042105,
    # Major cities
    "london": 102257491, "paris": 105259460, "berlin": 106967730,
    "amsterdam": 102011674, "munich": 100477049, "münchen": 100477049,
    "madrid": 105383020, "barcelona": 104918990, "milan": 103873152,
    "brussels": 100547541, "vienna": 106405756, "wien": 106405756,
    "prague": 104752280, "praha": 104752280,
    "warsaw": 105098144, "warszawa": 105098144,
    "stockholm": 106691059, "copenhagen": 105515856,
    "dublin": 104738078, "lisbon": 104810656, "lisboa": 104810656,
    "zurich": 106693272, "zürich": 106693272,
    # US (commonly needed)
    "united states": 103644278, "usa": 103644278, "us": 103644278,
    "new york": 105080838, "san francisco": 102277331,
    "los angeles": 102448103, "chicago": 103112676,
}

# Industry codes (V1 — commonly used in Sales Navigator)
INDUSTRIES = {
    116: "Logistics and Supply Chain",
    92: "Transportation/Trucking/Railroad",
    93: "Warehousing",
    87: "Package/Freight Delivery",
    95: "Maritime",
    94: "Airlines/Aviation",
    134: "Import and Export",
    27: "Retail",
    23: "Food Production",
    53: "Automotive",
    55: "Machinery",
    48: "Construction",
    56: "Mining & Metals",
    57: "Oil & Energy",
    122: "Facilities Services",
    4: "Computer Software",
    6: "Information Technology and Services",
    14: "Pharmaceuticals",
    25: "Manufacturing",
    26: "Consumer Goods",
    44: "Banking",
    47: "Insurance",
    43: "Financial Services",
    96: "Telecommunications",
    1: "Defense & Space",
    12: "Hospital & Health Care",
}
INDUSTRIES_BY_NAME = {}
for _id, _name in INDUSTRIES.items():
    INDUSTRIES_BY_NAME[_name.lower()] = _id
    _first = _name.lower().split("/")[0].split("&")[0].strip()
    if _first not in INDUSTRIES_BY_NAME:
        INDUSTRIES_BY_NAME[_first] = _id


# =============================================================================
# Rest.li Encoding/Decoding
# =============================================================================

def _restli_encode(text: str) -> str:
    """Double URL-encode text for Rest.li format inside Sales Nav URLs."""
    first = quote(text, safe="")
    second = quote(first, safe="")
    return second


def _restli_decode(text: str) -> str:
    """Double URL-decode text from Sales Nav URLs."""
    first = unquote(text)
    second = unquote(first)
    return second


def _single_decode(text: str) -> str:
    """Single URL-decode."""
    return unquote(text)


# =============================================================================
# Parser — extract filters from a Sales Navigator URL
# =============================================================================

def _parse_restli_list(s: str) -> list:
    """Parse a Rest.li List(...) into a list of raw strings (one per item)."""
    s = s.strip()
    if s.startswith("List(") and s.endswith(")"):
        s = s[5:-1]
    else:
        return []

    items = []
    depth = 0
    current = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        items.append("".join(current).strip())
    return [i for i in items if i]


def _parse_restli_object(s: str) -> dict:
    """Parse a Rest.li object (...) into a dict of key:value."""
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]

    result = {}
    depth = 0
    current = []
    for ch in s:
        if ch in "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            _parse_kv("".join(current).strip(), result)
            current = []
        else:
            current.append(ch)
    if current:
        _parse_kv("".join(current).strip(), result)
    return result


def _parse_kv(kv_str: str, result: dict):
    """Parse a key:value pair where value may contain nested structures."""
    idx = kv_str.find(":")
    if idx == -1:
        return
    key = kv_str[:idx].strip()
    value = kv_str[idx + 1:].strip()
    result[key] = value


def parse_url(url: str) -> dict:
    """
    Parse a Sales Navigator URL into a structured dict.

    Returns:
        {
            "keywords": str or None,
            "filters": {
                "CURRENT_COMPANY": [{"id": ..., "text": ..., "selectionType": ...}, ...],
                "SENIORITY_LEVEL": [...],
                ...
            },
            "recentSearchParam": str or None,
            "sessionId": str or None,
        }
    """
    query_str = None
    for prefix in ["#query=", "?query=", "#query%3D", "?query%3D"]:
        idx = url.find(prefix)
        if idx != -1:
            query_str = url[idx + len(prefix):]
            break

    if query_str is None:
        raise ValueError("Could not find query= in URL")

    depth = 0
    query_end = len(query_str)
    for i, ch in enumerate(query_str):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "&" and depth == 0:
            query_end = i
            break
    remaining = query_str[query_end:]
    query_str = query_str[:query_end]

    query_str = _single_decode(query_str)

    top = _parse_restli_object(query_str)

    result = {
        "keywords": None,
        "filters": {},
        "recentSearchParam": top.get("recentSearchParam"),
        "sessionId": None,
    }

    if "keywords" in top:
        result["keywords"] = _single_decode(top["keywords"])

    if "&sessionId=" in remaining:
        sid_start = remaining.index("&sessionId=") + len("&sessionId=")
        sid_end = remaining.find("&", sid_start)
        if sid_end == -1:
            sid_end = len(remaining)
        result["sessionId"] = _single_decode(remaining[sid_start:sid_end])

    filters_str = top.get("filters", "")
    if filters_str.startswith("List("):
        filter_items = _parse_restli_list(filters_str)
        for item_str in filter_items:
            filter_obj = _parse_restli_object(item_str)
            filter_type = filter_obj.get("type", "")
            values_str = filter_obj.get("values", "List()")
            values = []
            for val_str in _parse_restli_list(values_str):
                val_obj = _parse_restli_object(val_str)
                entry = {}
                if "id" in val_obj:
                    entry["id"] = _single_decode(val_obj["id"])
                if "text" in val_obj:
                    entry["text"] = _single_decode(val_obj["text"])
                if "selectionType" in val_obj:
                    entry["selectionType"] = val_obj["selectionType"]
                values.append(entry)
            result["filters"][filter_type] = values

    return result


# =============================================================================
# Builder — construct a Sales Navigator URL from filters
# =============================================================================

class SalesNavSearch:
    """Build and manipulate Sales Navigator search URLs."""

    BASE_URL = "https://www.linkedin.com/sales/search/people"

    def __init__(self):
        self.filters = {}
        self.keywords = None
        self.recent_search_id = None
        self.session_id = None

    @classmethod
    def from_url(cls, url: str) -> "SalesNavSearch":
        """Parse an existing Sales Navigator URL into a SalesNavSearch object."""
        parsed = parse_url(url)
        obj = cls()
        obj.filters = parsed["filters"]
        obj.keywords = parsed["keywords"]
        obj.session_id = parsed["sessionId"]
        return obj

    def _add_filter_values(self, filter_type: str, values: list, replace: bool = False):
        if replace or filter_type not in self.filters:
            self.filters[filter_type] = []
        self.filters[filter_type].extend(values)

    def add_companies(self, companies, org_ids: dict = None, filter_type: str = "CURRENT_COMPANY",
                      selection_type: str = "INCLUDED"):
        org_ids = org_ids or {}
        if isinstance(companies, dict):
            org_ids.update(companies)
            companies = list(companies.keys())

        values = []
        for name in companies:
            entry = {"text": name, "selectionType": selection_type}
            org_id = org_ids.get(name)
            if org_id:
                if not org_id.startswith("urn:"):
                    org_id = f"urn:li:organization:{org_id}"
                entry["id"] = org_id
            values.append(entry)
        self._add_filter_values(filter_type, values)

    def remove_companies(self, names: list, filter_type: str = "CURRENT_COMPANY"):
        if filter_type in self.filters:
            names_lower = {n.lower() for n in names}
            self.filters[filter_type] = [
                v for v in self.filters[filter_type]
                if v.get("text", "").lower() not in names_lower
            ]

    def add_titles(self, titles: list, filter_type: str = "CURRENT_TITLE",
                   selection_type: str = "INCLUDED"):
        values = [{"text": t, "selectionType": selection_type} for t in titles]
        self._add_filter_values(filter_type, values)

    def add_seniority(self, levels, selection_type: str = "INCLUDED"):
        values = []
        for level in levels:
            if isinstance(level, int):
                sid = level
            else:
                sid = SENIORITY_BY_NAME.get(level.lower())
                if sid is None:
                    raise ValueError(f"Unknown seniority level: {level}. "
                                     f"Valid: {list(SENIORITY_LEVELS.values())}")
            values.append({
                "id": str(sid),
                "text": SENIORITY_LEVELS[sid],
                "selectionType": selection_type,
            })
        self._add_filter_values("SENIORITY_LEVEL", values)

    def add_functions(self, functions, selection_type: str = "INCLUDED"):
        values = []
        for func in functions:
            if isinstance(func, int):
                fid = func
            else:
                fid = FUNCTIONS_BY_NAME.get(func.lower())
                if fid is None:
                    raise ValueError(f"Unknown function: {func}. "
                                     f"Valid: {list(FUNCTIONS.values())}")
            values.append({
                "id": str(fid),
                "text": FUNCTIONS[fid],
                "selectionType": selection_type,
            })
        self._add_filter_values("FUNCTION", values)

    def add_regions(self, regions, selection_type: str = "INCLUDED",
                    filter_type: str = "REGION"):
        values = []
        if isinstance(regions, dict):
            for name, geo_id in regions.items():
                values.append({
                    "id": str(geo_id),
                    "text": name,
                    "selectionType": selection_type,
                })
        else:
            for region in regions:
                if isinstance(region, int):
                    name = next((k for k, v in GEO_URNS.items() if v == region), str(region))
                    values.append({
                        "id": str(region),
                        "text": name.title(),
                        "selectionType": selection_type,
                    })
                else:
                    geo_id = GEO_URNS.get(region.lower())
                    if geo_id is None:
                        raise ValueError(f"Unknown region: {region}. "
                                         f"Use a dict {{name: geo_urn_id}} for custom regions.")
                    values.append({
                        "id": str(geo_id),
                        "text": region,
                        "selectionType": selection_type,
                    })
        self._add_filter_values(filter_type, values)

    def add_industries(self, industries, selection_type: str = "INCLUDED"):
        values = []
        for ind in industries:
            if isinstance(ind, int):
                iid = ind
                name = INDUSTRIES.get(iid, str(iid))
            else:
                iid = INDUSTRIES_BY_NAME.get(ind.lower())
                if iid is None:
                    raise ValueError(f"Unknown industry: {ind}. "
                                     f"Known: {list(INDUSTRIES.values())}")
                name = INDUSTRIES[iid]
            values.append({
                "id": str(iid),
                "text": name,
                "selectionType": selection_type,
            })
        self._add_filter_values("INDUSTRY", values)

    def add_company_headcount(self, sizes, selection_type: str = "INCLUDED"):
        values = []
        for size in sizes:
            code = size.upper()
            if code not in COMPANY_HEADCOUNT:
                raise ValueError(f"Unknown headcount code: {size}. "
                                 f"Valid: {COMPANY_HEADCOUNT}")
            values.append({
                "id": code,
                "text": COMPANY_HEADCOUNT[code],
                "selectionType": selection_type,
            })
        self._add_filter_values("COMPANY_HEADCOUNT", values)

    def set_changed_jobs(self, enabled: bool = True):
        if enabled:
            self.filters["RECENTLY_CHANGED_JOBS"] = [
                {"id": "RPC", "text": "Changed jobs", "selectionType": "INCLUDED"}
            ]
        else:
            self.filters.pop("RECENTLY_CHANGED_JOBS", None)

    def set_posted_on_linkedin(self, enabled: bool = True):
        if enabled:
            self.filters["POSTED_ON_LINKEDIN"] = [
                {"id": "POL", "text": "Posted on LinkedIn", "selectionType": "INCLUDED"}
            ]
        else:
            self.filters.pop("POSTED_ON_LINKEDIN", None)

    def set_keywords(self, keywords: str):
        self.keywords = keywords

    def add_raw_filter(self, filter_type: str, values: list):
        self._add_filter_values(filter_type, values)

    # ---- URL Building ----

    def _encode_value(self, entry: dict, filter_type: str = "") -> str:
        parts = []
        if "id" in entry:
            encoded_id = _restli_encode(entry["id"])
            parts.append(f"id:{encoded_id}")
        if "text" in entry:
            encoded_text = _restli_encode(entry["text"])
            parts.append(f"text:{encoded_text}")
        if "selectionType" in entry:
            parts.append(f"selectionType:{entry['selectionType']}")
        if filter_type in ("CURRENT_COMPANY", "PAST_COMPANY") and "id" in entry:
            parts.append("parent:(id:0)")
        return "(" + ",".join(parts) + ")"

    def _encode_filter(self, filter_type: str, values: list) -> str:
        encoded_values = ",".join(self._encode_value(v, filter_type) for v in values)
        return f"(type:{filter_type},values:List({encoded_values}))"

    def build_url(self) -> str:
        query_parts = []
        query_parts.append("recentSearchParam:(doLogHistory:true)")

        if self.keywords:
            encoded_kw = quote(self.keywords, safe="")
            query_parts.append(f"keywords:{encoded_kw}")

        if self.filters:
            filter_strs = []
            for ftype, values in self.filters.items():
                if values:
                    filter_strs.append(self._encode_filter(ftype, values))
            if filter_strs:
                query_parts.append(f"filters:List({','.join(filter_strs)})")

        query_str = ",".join(query_parts)
        encoded_query = quote(f"({query_str})", safe="%()")
        url = f"{self.BASE_URL}?query={encoded_query}&sessionId=0&viewAllFilters=true"
        return url

    # ---- Export / Import ----

    def list_companies(self, filter_type: str = "CURRENT_COMPANY") -> list:
        companies = []
        for entry in self.filters.get(filter_type, []):
            companies.append({
                "name": entry.get("text", ""),
                "org_id": entry.get("id", ""),
                "selection_type": entry.get("selectionType", "INCLUDED"),
            })
        return companies

    def export_companies_csv(self, filepath: str = None, filter_type: str = "CURRENT_COMPANY") -> str:
        companies = self.list_companies(filter_type)
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "org_id", "selection_type"])
        writer.writeheader()
        writer.writerows(companies)
        csv_str = output.getvalue()
        if filepath:
            with open(filepath, "w") as f:
                f.write(csv_str)
        return csv_str

    def import_companies_csv(self, filepath_or_string: str, filter_type: str = "CURRENT_COMPANY"):
        try:
            with open(filepath_or_string, "r") as f:
                content = f.read()
        except (FileNotFoundError, OSError):
            content = filepath_or_string

        reader = csv.DictReader(StringIO(content))
        org_ids = {}
        names = []
        for row in reader:
            name = row.get("name", "").strip()
            org_id = row.get("org_id", "").strip()
            if name:
                names.append(name)
                if org_id:
                    org_ids[name] = org_id
        self.add_companies(names, org_ids=org_ids, filter_type=filter_type)

    def summary(self) -> str:
        lines = ["Sales Navigator Search Summary", "=" * 40]
        if self.keywords:
            lines.append(f"Keywords: {self.keywords}")
        for ftype, values in self.filters.items():
            texts = [v.get("text", v.get("id", "?")) for v in values]
            if len(texts) <= 5:
                lines.append(f"{ftype}: {', '.join(texts)}")
            else:
                lines.append(f"{ftype}: {', '.join(texts[:5])} ... (+{len(texts)-5} more)")
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def _cli_parse(args):
    if len(args) < 1:
        print("Usage: sales_nav_url_builder.py parse <URL>")
        return
    url = args[0]
    search = SalesNavSearch.from_url(url)
    print(search.summary())
    print()

    companies = search.list_companies()
    if companies:
        print(f"\nCompanies ({len(companies)}):")
        for c in companies:
            org = f" [{c['org_id']}]" if c["org_id"] else ""
            sel = f" (EXCLUDED)" if c["selection_type"] == "EXCLUDED" else ""
            print(f"  - {c['name']}{org}{sel}")


def _cli_export(args):
    if len(args) < 2:
        print("Usage: sales_nav_url_builder.py export <URL> <output.csv>")
        return
    url, filepath = args[0], args[1]
    search = SalesNavSearch.from_url(url)
    search.export_companies_csv(filepath)
    companies = search.list_companies()
    print(f"Exported {len(companies)} companies to {filepath}")


def _cli_build_demo(args):
    search = SalesNavSearch()
    search.add_companies(["BMW", "Siemens", "Volkswagen Group"])
    search.add_titles(["VP of Logistics", "Head of Supply Chain"])
    search.add_seniority(["Director", "VP", "CXO"])
    search.add_functions(["Operations", "Purchasing"])
    search.add_regions(["Germany", "Netherlands"])
    search.set_changed_jobs(True)
    print("Demo URL:")
    print(search.build_url())
    print()
    print(search.summary())


def main():
    if len(sys.argv) < 2:
        print("Sales Navigator URL Builder")
        print()
        print("Commands:")
        print("  parse <URL>              Parse and display URL contents")
        print("  export <URL> <file.csv>  Export companies from URL to CSV")
        print("  demo                     Build a demo URL")
        print()
        print("Python API:")
        print("  from sales_nav_url_builder import SalesNavSearch")
        print("  search = SalesNavSearch.from_url(url)")
        print("  search.add_companies(['BMW', 'Siemens'])")
        print("  print(search.build_url())")
        return

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "parse":
        _cli_parse(rest)
    elif cmd == "export":
        _cli_export(rest)
    elif cmd == "demo":
        _cli_build_demo(rest)
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
