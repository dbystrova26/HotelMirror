# 🏨 Hotel Mirror — Lease Intelligence Agent

Finds hotels and buildings available for long-term lease across 14 European markets.
Outputs clean, structured data: property details, landlord contacts, broker contacts.

No scoring. No priorities. Just the data.

---

## What it does

```
Web search  →  Parse listings  →  Full contact details  →  JSON + CSV
(agentic loop)                    landlord + broker         ready to import
```

---

## Markets

| Code | Country        | Code | Country        |
|------|---------------|------|---------------|
| DE   | Germany        | CZ   | Czech Republic |
| NL   | Netherlands    | GB   | United Kingdom |
| FR   | France         | IE   | Ireland        |
| BE   | Belgium        | IT   | Italy          |
| LU   | Luxembourg     | ES   | Spain          |
| CH   | Switzerland    | PT   | Portugal       |
| PL   | Poland         | GR   | Greece         |

---

## Output fields

```
property_name · address · city · country_code · property_type
rooms · sqm · floors · year_built
lease_term · asking_rent · available_from
landlord_name · landlord_company · landlord_email · landlord_phone · landlord_website
broker_name · broker_company · broker_email · broker_phone
source_url · source_name · notes · run_timestamp
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
#    Option A — shell environment (recommended for CI/scripts)
export ANTHROPIC_API_KEY=sk-ant-...

#    Option B — .env file (recommended for local dev)
cp .env.example .env
# edit .env and paste your key, then the agent loads it automatically

# 3. Run
python agent.py
```

Or use the guided setup script:
```bash
bash setup.sh
```

Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys.
The key is **never hardcoded** — always read from environment or `.env`.

---

## Usage

**All 14 markets:**
```bash
python agent.py
```

**Focused search:**
```bash
python agent.py \
  --countries DE NL CH \
  --type Hotel \
  --min-units 80 \
  --city Frankfurt \
  --notes "15+ year lease"
```

**With Slack alerts:**
```bash
python agent.py \
  --countries GB IE \
  --slack https://hooks.slack.com/services/YOUR/WEBHOOK
```

**Custom output folder:**
```bash
python agent.py --output ./reports
```

---

## Arguments

| Argument | Default | Description |
|---|---|---|
| `--countries` | all 14 | Space-separated ISO codes |
| `--type` | any | `Hotel`, `Apart-hotel`, `Office conversion`, `Residential building`, `Mixed-use` |
| `--min-units` | 0 | Minimum rooms / units |
| `--city` | any | City or region focus |
| `--notes` | — | Extra search criteria |
| `--max` | 12 | Max results per run |
| `--slack` | — | Slack webhook for alerts |
| `--output` | `.` | Directory for JSON + CSV files |

---

## Sources searched

Christie & Co · JLL Hotels · CBRE Hotels · Savills · BNP Paribas RE · Colliers · Knight Frank · HCRE · Hospitality Advisors · Cushman & Wakefield · Immobilienscout24 · Funda · SeLoger · Immowelt · Rightmove Commercial · Idealista · Immobiliare.it

---

## Frontend

Open `hotel_mirror.html` in a browser for the full visual interface — same search engine, results displayed as a sortable web table with all contact details in one view.

---

## Stack

```
anthropic SDK    Claude claude-sonnet-4-6 + web_search tool
                 Agentic loop (tool_use → tool_result → end_turn)
```
