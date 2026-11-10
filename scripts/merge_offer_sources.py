import json, os

RAW_FT_PATH = "data/offers/raw_offers.json"
JOBSPY_PATH = "data/offers/jobspy_offers.json"
MERGED_PATH = "data/offers/merged_offers.json"

def normalize_france_travail(raw_offers):
    normalized = []
    for o in raw_offers:
        normalized.append({
            "id": f"ft_{o['id']}",
            "source": "france_travail",
            "title": o.get("intitule"),
            "company": (o.get("entreprise") or {}).get("nom"),
            "location": (o.get("lieuTravail") or {}).get("libelle"),
            "description": o.get("description", ""),
            "url": (o.get("origineOffre") or {}).get("urlOrigine"),
            "date_posted": o.get("dateCreation"),
            "is_apprenticeship": o.get("alternance", False),
            "accessible_disability": o.get("accessibleTH", False),
            "publishable": True,  # official open government data -- safe to publish
        })
    return normalized

def load_france_travail():
    # France Travail's "Offres d'emploi v2" API is now restricted ("accessible sous
    # conditions"), so this file may not exist. That is fine: skip it, don't crash.
    if not os.path.exists(RAW_FT_PATH):
        print(f"{RAW_FT_PATH} not found -- skipping France Travail (API access restricted).")
        return []
    with open(RAW_FT_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_france_travail(raw.get("offers", []))

def load_jobspy():
    if not os.path.exists(JOBSPY_PATH):
        print(f"{JOBSPY_PATH} not found -- skipping jobspy.")
        return []
    with open(JOBSPY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [
        {**o, "is_apprenticeship": False, "accessible_disability": False,
         "publishable": False}  # scraped content -- never published
        for o in data["offers"]
    ]

def main():
    ft_offers = load_france_travail()
    jobspy_offers = load_jobspy()

    merged = ft_offers + jobspy_offers
    if not merged:
        raise SystemExit("No offers from any source. Run fetch_offers_jobspy.py first.")
    print(f"Merged {len(ft_offers)} France Travail + {len(jobspy_offers)} jobspy = {len(merged)} total")

    os.makedirs("data/offers", exist_ok=True)
    with open(MERGED_PATH, "w", encoding="utf-8") as f:
        json.dump({"offers": merged}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {MERGED_PATH} ({len(merged)} offers) -- gitignored, local only")

if __name__ == "__main__":
    main()
