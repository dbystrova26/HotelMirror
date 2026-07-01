"""
Hotel Mirror — Lease Intelligence Agent
----------------------------------------
Searches European hotel & building lease markets for serviced apartment operators.
No scoring. No priorities. Just clean, structured data:
property details · landlord contacts · broker contacts · source links.

Output: JSON + CSV ready for import into Notion / Airtable / Google Sheets.

Markets: DE · NL · FR · BE · LU · CH · CZ · GB · IE · IT · ES · PT · GR · PL
"""

import os
import json
import csv
import re
import datetime
import time
import argparse

# Load .env file if present (requires python-dotenv, installed via requirements.txt)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — rely on env vars set in shell

import anthropic

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

COUNTRIES = {
    "DE": "Germany",
    "NL": "Netherlands",
    "FR": "France",
    "BE": "Belgium",
    "LU": "Luxembourg",
    "CH": "Switzerland",
    "CZ": "Czech Republic",
    "GB": "United Kingdom",
    "IE": "Ireland",
    "IT": "Italy",
    "ES": "Spain",
    "PT": "Portugal",
    "GR": "Greece",
    "PL": "Poland",
}

BROKERS = (
    "Christie & Co, JLL Hotels & Hospitality, CBRE Hotels, Savills Hotels, "
    "BNP Paribas Real Estate, Colliers Hotels, Knight Frank Hotels, "
    "HCRE, Hospitality Advisors, Cushman & Wakefield, Streimer, "
    "Immobilienscout24, Funda, SeLoger, Immowelt, Rightmove Commercial, "
    "Idealista, Immobiliare.it"
)

SYSTEM_PROMPT = f"""You are a specialist real estate researcher for European serviced apartment operators
(Bob W, Zoku, Wilde Aparthotels, Edyn, Numa, Sonder).

Your task: find hotels, apart-hotels, and large buildings available for LONG-TERM LEASE
(master lease or management contract). The operator NEVER buys — lease only.

Search these broker portals and property sites: {BROKERS}

Return ONLY a valid JSON array — no markdown fences, no preamble, no explanation.
Each object must have exactly these keys (use null if unknown):

{{
  "property_name":      string,
  "address":            string,
  "city":               string,
  "country_code":       "DE"|"NL"|"FR"|"BE"|"LU"|"CH"|"CZ"|"GB"|"IE"|"IT"|"ES"|"PT"|"GR"|"PL",
  "property_type":      "Hotel"|"Apart-hotel"|"Office conversion"|"Residential building"|"Mixed-use",
  "rooms":              string,
  "sqm":                string,
  "floors":             string,
  "year_built":         string,
  "lease_term":         string,
  "asking_rent":        string,
  "available_from":     string,
  "landlord_name":      string,
  "landlord_company":   string,
  "landlord_email":     string,
  "landlord_phone":     string,
  "landlord_website":   string,
  "broker_name":        string,
  "broker_company":     string,
  "broker_email":       string,
  "broker_phone":       string,
  "source_url":         string,
  "source_name":        string,
  "notes":              string
}}
"""

# ─────────────────────────────────────────────
# ANTHROPIC CLIENT
# ─────────────────────────────────────────────

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not _api_key:
    raise SystemExit(
        "\n  ✗  ANTHROPIC_API_KEY not set.\n\n"
        "  Set it in your shell:\n"
        "    export ANTHROPIC_API_KEY=sk-ant-...\n\n"
        "  Or create a .env file:\n"
        "    cp .env.example .env   # then add your key\n\n"
        "  Get a key at: https://console.anthropic.com → API Keys\n"
    )

client = anthropic.Anthropic(api_key=_api_key)

# ─────────────────────────────────────────────
# AGENTIC SEARCH LOOP
# ─────────────────────────────────────────────

def search(user_message: str, max_iterations: int = 8) -> str:
    """
    Multi-turn agentic loop with web_search tool.
    Runs until stop_reason == end_turn or max iterations reached.
    """
    messages = [{"role": "user", "content": user_message}]
    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    for i in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=5000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return "".join(
                b.text for b in response.content if b.type == "text"
            )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": b.id, "content": ""}
                    for b in response.content if b.type == "tool_use"
                ],
            })
            continue

        # Unexpected stop — return whatever text we have
        return "".join(b.text for b in response.content if hasattr(b, "text"))

    return ""


# ─────────────────────────────────────────────
# PARSE JSON FROM RESPONSE
# ─────────────────────────────────────────────

def parse_listings(raw: str) -> list[dict]:
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw).strip()
    s, e = raw.find("["), raw.rfind("]")
    if s == -1 or e == -1:
        return []
    try:
        return json.loads(raw[s : e + 1])
    except json.JSONDecodeError as err:
        print(f"  ⚠  JSON parse error: {err}")
        return []


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

FIELD_ORDER = [
    "property_name", "address", "city", "country_code", "property_type",
    "rooms", "sqm", "floors", "year_built",
    "lease_term", "asking_rent", "available_from",
    "landlord_name", "landlord_company", "landlord_email", "landlord_phone", "landlord_website",
    "broker_name", "broker_company", "broker_email", "broker_phone",
    "source_url", "source_name", "notes",
    "run_timestamp",
]

def stamp(listings: list[dict]) -> list[dict]:
    ts = datetime.datetime.utcnow().isoformat()
    for l in listings:
        l["run_timestamp"] = ts
        # Ensure all fields exist
        for f in FIELD_ORDER:
            l.setdefault(f, None)
    return listings

def save_json(listings: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(listings, f, indent=2, ensure_ascii=False)
    print(f"  💾  JSON  →  {path}")

def save_csv(listings: list[dict], path: str):
    if not listings:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_ORDER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(listings)
    print(f"  💾  CSV   →  {path}")


# ─────────────────────────────────────────────
# OPTIONAL: SLACK ALERT
# ─────────────────────────────────────────────

def slack_alert(listing: dict, webhook: str):
    try:
        import urllib.request
        text = (
            f"🏨 *{listing.get('property_name','?')}* — "
            f"{listing.get('city','?')}, {listing.get('country_code','?')}\n"
            f"Type: {listing.get('property_type','?')} · "
            f"Rooms: {listing.get('rooms','?')} · "
            f"Rent: {listing.get('asking_rent','?')}\n"
            f"Landlord: {listing.get('landlord_name','?')} "
            f"({listing.get('landlord_company','?')}) "
            f"{listing.get('landlord_email') or listing.get('landlord_phone','')}\n"
            f"Broker: {listing.get('broker_name','?')} "
            f"({listing.get('broker_company','?')}) "
            f"{listing.get('broker_email') or listing.get('broker_phone','')}\n"
            f"Source: {listing.get('source_url','?')}"
        )
        body = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            webhook, data=body, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        print(f"  ⚠  Slack alert failed: {exc}")


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

def run(
    countries: list[str] | None = None,
    property_type: str = "",
    min_units: int = 0,
    city: str = "",
    notes: str = "",
    slack_webhook: str = "",
    output_dir: str = ".",
    max_results: int = 12,
) -> list[dict]:

    countries = countries or list(COUNTRIES.keys())
    country_str = ", ".join(COUNTRIES[c] for c in countries if c in COUNTRIES)

    print()
    print("══════════════════════════════════════════════════")
    print("  HOTEL MIRROR  —  Lease Intelligence Agent")
    print("══════════════════════════════════════════════════")
    print(f"  Markets  : {country_str}")
    if property_type: print(f"  Type     : {property_type}")
    if min_units:     print(f"  Min units: {min_units}")
    if city:          print(f"  City     : {city}")
    if notes:         print(f"  Notes    : {notes}")
    print()

    # Build search query
    filters = []
    if property_type: filters.append(f"property type: {property_type}")
    if min_units:     filters.append(f"minimum {min_units} units/rooms")
    if city:          filters.append(f"city or region: {city}")
    if notes:         filters.append(notes)

    query = (
        f"Find hotels and buildings available for long-term lease "
        f"(master lease or management contract) for serviced apartment operators in: {country_str}. "
        + (f"Filters: {'; '.join(filters)}. " if filters else "")
        + f"Search all major broker portals and property sites. "
        f"Return up to {max_results} results as a JSON array with full landlord and broker contact details."
    )

    print("  🔍  Searching the web…")
    raw = search(query)

    listings = parse_listings(raw)
    if not listings:
        print("  ⚠  No listings found. Try broader criteria.")
        return []

    listings = stamp(listings)
    print(f"  ✅  {len(listings)} listing(s) found.\n")

    # Print summary table to terminal
    print(f"  {'PROPERTY':<35} {'CITY':<18} {'CC':<4} {'ROOMS':<8} {'RENT'}")
    print(f"  {'─'*35} {'─'*18} {'─'*4} {'─'*8} {'─'*20}")
    for l in listings:
        print(
            f"  {str(l.get('property_name','?'))[:34]:<35} "
            f"{str(l.get('city','?'))[:17]:<18} "
            f"{str(l.get('country_code','?')):<4} "
            f"{str(l.get('rooms','?'))[:7]:<8} "
            f"{str(l.get('asking_rent','?'))[:25]}"
        )

    # Slack alerts
    if slack_webhook:
        print(f"\n  📣  Sending {len(listings)} Slack alert(s)…")
        for l in listings:
            slack_alert(l, slack_webhook)
            time.sleep(0.3)

    # Export
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    print()
    save_json(listings, f"{output_dir}/hotel_mirror_{ts}.json")
    save_csv(listings,  f"{output_dir}/hotel_mirror_{ts}.csv")
    print()
    print("  ✅  Done.\n")

    return listings


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hotel Mirror — lease intelligence agent for serviced apartment operators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py
  python agent.py --countries DE NL FR --type Hotel --min-units 80
  python agent.py --city Frankfurt --notes "15+ year lease preferred"
  python agent.py --countries GB IE --slack https://hooks.slack.com/services/...
        """,
    )
    parser.add_argument(
        "--countries", nargs="+", default=list(COUNTRIES.keys()),
        metavar="CC",
        help=f"ISO country codes (default: all). Options: {' '.join(COUNTRIES.keys())}",
    )
    parser.add_argument("--type",      default="", metavar="TYPE",    help="Property type filter")
    parser.add_argument("--min-units", default=0,  type=int,          help="Minimum unit/room count")
    parser.add_argument("--city",      default="", metavar="CITY",    help="City or region focus")
    parser.add_argument("--notes",     default="", metavar="TEXT",    help="Additional search criteria")
    parser.add_argument("--max",       default=12, type=int,          help="Max results (default 12)")
    parser.add_argument("--slack",     default="", metavar="URL",     help="Slack webhook URL")
    parser.add_argument("--output",    default=".", metavar="DIR",    help="Output directory (default: .)")

    args = parser.parse_args()

    run(
        countries=args.countries,
        property_type=args.type,
        min_units=args.min_units,
        city=args.city,
        notes=args.notes,
        slack_webhook=args.slack,
        output_dir=args.output,
        max_results=args.max,
    )
