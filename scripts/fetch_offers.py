import json, os, sys, time
import requests

# France Travail "Offres d'emploi v2" API -- OAuth2 client_credentials flow.
# "stage" is NOT in this API's contract-type taxonomy (a stage is governed by a
# school convention de stage, not an employment contract), so we search by
# keyword (motsCles) and only use a contract-type filter if one happens to match.

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
REFERENTIEL_CONTRATS_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/typesContrats"

CLIENT_ID = os.environ["FRANCETRAVAIL_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["FRANCETRAVAIL_CLIENT_SECRET"].strip()
SCOPE = "api_offresdemploiv2 o2dsoffre"

# Edit this to your own search. No commune/distance filter = nationwide.
SEARCH_PARAMS = {
    "motsCles": "stage informatique",
    "sort": "1",                 # sort by date, most recent first
    "range": "0-49",             # first 50 results
}

def get_access_token(retries=4, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "scope": SCOPE,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=(10, 20),
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  token request attempt {attempt}/{retries} failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"  response body: {e.response.text[:500]}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Could not obtain access token after {retries} attempts") from last_error

def try_resolve_contract_type_code(token, label_substring="stage"):
    """Best-effort only. Returns None (never raises) if the endpoint is
    unreachable or no match exists -- 'stage' has no match in this taxonomy."""
    try:
        resp = requests.get(
            REFERENTIEL_CONTRATS_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=(10, 20),
        )
        resp.raise_for_status()
        all_types = resp.json()
        print("Available contract types:", json.dumps(all_types, ensure_ascii=False))
        for t in all_types:
            if label_substring.lower() in t.get("libelle", "").lower():
                print(f"Resolved '{label_substring}' -> code '{t['code']}' ({t['libelle']})")
                return t["code"]
        print(f"No contract type matches '{label_substring}' -- proceeding with keyword search only "
              f"(this is expected: 'stage' is not part of this API's contract-type taxonomy).")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch contract-type referentiel ({e}) -- proceeding with keyword search only.")
        return None

def search_offers(token, retries=4, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                SEARCH_URL,
                params=SEARCH_PARAMS,
                headers={"Authorization": f"Bearer {token}"},
                timeout=(10, 30),
            )
            print(f"  search attempt {attempt}/{retries}: HTTP {resp.status_code}, "
                  f"body starts with: {resp.text[:200]!r}")
            # 206 (Partial Content) is a normal paginated success; 204 = zero matches.
            if resp.status_code == 204:
                return {"resultats": []}
            if resp.status_code not in (200, 206):
                resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  search attempt {attempt}/{retries} failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"  response body: {e.response.text[:500]}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Could not search offers after {retries} attempts") from last_error

def main():
    print("Requesting access token...")
    token = get_access_token()

    print("Checking whether a 'stage' contract type code exists...")
    code = try_resolve_contract_type_code(token, "stage")
    if code:
        SEARCH_PARAMS["typeContrat"] = code

    print("Got token, searching offers...")
    data = search_offers(token)
    offers = data.get("resultats", [])
    print(f"Found {len(offers)} offers")

    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/raw_offers.json", "w") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "search_params": SEARCH_PARAMS, "offers": offers}, f, indent=2, ensure_ascii=False)
    print("Wrote data/offers/raw_offers.json")
    if offers:
        print("First offer preview:", json.dumps(offers[0], ensure_ascii=False, indent=2)[:800])

if __name__ == "__main__":
    main()
