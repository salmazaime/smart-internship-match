import json, os, time
import requests

# Source: Adzuna job search API (developer.adzuna.com), country "fr".
# Replaces France Travail's "Offres d'emploi v2", which is not available in the
# francetravail.io catalogue at the moment. Same output file and same downstream
# pipeline: this script still writes data/offers/raw_offers.json.
#
# Note: Adzuna returns a SHORT description snippet (a few hundred characters), not
# the full posting. Skill extraction therefore sees less text than it would with
# full descriptions. Worth stating as a limitation in the report.

COUNTRY = "fr"
SEARCH_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"

APP_ID = os.environ["ADZUNA_APP_ID"].strip()
APP_KEY = os.environ["ADZUNA_APP_KEY"].strip()

# Edit this to your own search.
SEARCH_PARAMS = {
    "what": "stage informatique",
    "results_per_page": 50,
    "sort_by": "date",
    "content-type": "application/json",
}

def search_offers(retries=4, backoff=5):
    last_error = None
    params = {**SEARCH_PARAMS, "app_id": APP_ID, "app_key": APP_KEY}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(SEARCH_URL, params=params, timeout=(10, 30))
            print(f"  search attempt {attempt}/{retries}: HTTP {resp.status_code}, "
                  f"body starts with: {resp.text[:200]!r}")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  search attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Could not search offers after {retries} attempts") from last_error

def main():
    print("Searching Adzuna...")
    data = search_offers()
    offers = data.get("results", [])
    print(f"Found {len(offers)} offers (total matching on Adzuna: {data.get('count')})")

    os.makedirs("data/offers", exist_ok=True)
    safe_params = {k: v for k, v in SEARCH_PARAMS.items()}
    with open("data/offers/raw_offers.json", "w") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "source": "adzuna", "search_params": safe_params, "offers": offers},
                  f, indent=2, ensure_ascii=False)
    print("Wrote data/offers/raw_offers.json")
    if offers:
        print("First offer preview:", json.dumps(offers[0], ensure_ascii=False, indent=2)[:800])

if __name__ == "__main__":
    main()
