# 🏨 Hotel Mirror — Lease Intelligence Agent

AI agent that finds hotels and buildings available for **long-term lease** across 21 countries and ~110 target cities. Landlord and broker contacts in one sortable table.

Built for serviced-apartment and extended-stay operators that **lease, never buy**.

---

## What it does

```
Web search (local-language terms)  →  Validate & filter to target cities  →  Table / JSON / CSV
     Claude (primary)                      up to 100 listings per run          landlord + broker contacts
     OpenAI (auto-fallback)
```

- Searches property portals, business-transfer sites, broker pages, and hospitality news **in each country's language** — "Hotel zu verpachten", "hôtel location-gérance", "hotel in affitto", "hotel en alquiler", "hotel te huur"…
- Includes Pacht, location-gérance, affitto di ramo d'azienda, leasehold sales, and landlord operator-searches
- Every result must carry a real `source_url`; unknown fields are `null` — nothing invented
- **Automatic OpenAI fallback** if Anthropic fails (no credit, rate limit, outage)

---

## Target markets

Searches are restricted to these target cities; listings outside them are flagged or discarded.

| Region | Cities |
|---|---|
| 🇩🇪 Germany | Berlin, Bonn, Bremen, Cologne, Dresden, Düsseldorf, Frankfurt, Freiburg, Hamburg, Heidelberg, Leipzig, Munich, Nuremberg, Stuttgart |
| 🇦🇹 Austria | Graz, Innsbruck, Kitzbühel, Salzburg, Vienna |
| 🇨🇭 Switzerland | Basel, Bern, Geneva, Lausanne, Lugano, Luzern, Zurich |
| 🇳🇱🇧🇪🇱🇺 Benelux | Amsterdam, Rotterdam, The Hague, Utrecht, Haarlem, Groningen, Maastricht, Antwerp, Brussels, Bruges, Ghent, Luxembourg |
| 🇫🇷 France | Paris, Lyon, Marseille, Bordeaux, Nice, Cannes, Lille, Nantes, Montpellier, Toulouse, Strasbourg, Aix-en-Provence |
| 🇬🇧🇮🇪 UK & Ireland | London, Manchester, Edinburgh, Birmingham, Bristol, Glasgow, Leeds, Liverpool, Newcastle, Oxford, York, Bath, Brighton, Cardiff, Belfast, Dublin |
| 🇮🇹 Italy | Rome, Milano, Florence, Venice, Bologna, Turin, Genoa, Napoli, Palermo, Verona |
| 🇪🇸🇵🇹 Iberia | Madrid, Barcelona, Valencia, Sevilla, Malaga, Marbella, Bilbao, San Sebastian, Alicante, Granada, Palma, Las Palmas, Lisbon, Porto, Funchal |
| 🇨🇿🇭🇺🇵🇱 Eastern Europe | Prague, Budapest, Krakow, Warsaw |
| 🇩🇰🇸🇪🇫🇮🇳🇴 Nordics | Copenhagen, Stockholm, Gothenburg, Helsinki, Oslo |
| 🇦🇪🇮🇱 Middle East | Dubai, Tel Aviv |

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

# 2. Set your API keys
cp .env.example .env
# edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...   (primary)
#   OPENAI_API_KEY=sk-...          (fallback, optional but recommended)
```

Keys are **never hardcoded** — always read from environment / `.env`.

---

## Run — web frontend

```bash
python app.py
# → open http://127.0.0.1:5000
```

Flask injects the keys into `hotel_mirror.html` at runtime. Toggle markets, set optional filters, hit **Search listings**. Results appear in a sortable table with landlord/broker contacts and source links. Search takes 30–90 s (multiple web-search rounds).

Sanity-check your keys anytime at `http://127.0.0.1:5000/debug`.

---

## Run — CLI agent

```bash
# All target markets
python agent.py

# Focused run
python agent.py --countries DE AT CH --type Hotel --min-units 50 --city Munich

# Options
--countries CC [CC ...]   ISO codes (default: all 21)
--type TYPE               Hotel / Apart-hotel / Office conversion / ...
--min-units N             Minimum rooms/units
--city CITY               Focus city
--notes TEXT              Extra criteria
--max N                   Max results (default 100)
--slack URL               Slack webhook for alerts
--output DIR              Output dir for JSON + CSV (default .)
```

Each run exports timestamped `hotel_mirror_YYYYMMDD_HHMMSS.json` + `.csv` — ready for Notion, Airtable, or Google Sheets.

---

## Deploy on Render

1. Push to GitHub — `render.yaml` is auto-detected (gunicorn + Flask)
2. Render → **New → Web Service** → connect the repo
3. Environment → add `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`
4. Deploy → share `https://<your-app>.onrender.com`

---

## Architecture notes

- `web_search_20250305` is a **server-side** Anthropic tool — the API runs searches itself. Long turns pause with `stop_reason: "pause_turn"`; the loop resumes by re-sending the assistant content until `end_turn`
- OpenAI fallback uses the **Responses API** with the built-in `web_search` tool
- `max_tokens: 16000` on both providers so large result sets don't truncate mid-JSON
- Off-market reality: institutional hotel-lease deals (Christie & Co, JLL, CBRE…) are not published — the broker quick-links bar in the frontend covers that channel; the agent covers everything public

---

## Stack

```
anthropic        Claude claude-sonnet-4-6 + server-side web_search
openai           gpt-4.1 via Responses API (fallback, no SDK — plain HTTPS)
flask + gunicorn Web frontend / Render deployment
python-dotenv    .env loading
```
