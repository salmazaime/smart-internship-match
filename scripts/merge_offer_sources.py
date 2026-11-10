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
            # Best-effort: these are France Travail's usual field names. If they
            # are missing in your real data they just stay None (no crash) --
            # check one offer in raw_offers.json and adjust if needed.
            "url": (o.get("origineOffre") or {}).get("urlOrigine"),
            "date_posted": o.get("dateCreation"),
            "is_apprenticeship": o.get("alternance", False),
            "accessible_disability": o.get("accessibleTH", False),
            "publishable": True,  # official open government data -- safe to publish
        })
    return normalized

def load_jobspy():
    if not os.path.exists(JOBSPY_PATH):
        print(f"{JOBSPY_PATH} not found -- skipping (fine if you didn't do Step 11b).")
        return []
    with open(JOBSPY_PATH) as f:
        data = json.load(f)
    return [
        {**o, "is_apprenticeship": False, "accessible_disability": False,
         "publishable": False}  # scraped content -- never published
        for o in data["offers"]
    ]

def main():
    with open(RAW_FT_PATH) as f:
        ft_raw = json.load(f)
    ft_offers = normalize_france_travail(ft_raw["offers"])
    jobspy_offers = load_jobspy()

    merged = ft_offers + jobspy_offers
    print(f"Merged {len(ft_offers)} France Travail + {len(jobspy_offers)} jobspy = {len(merged)} total")

    os.makedirs("data/offers", exist_ok=True)
    with open(MERGED_PATH, "w") as f:
        json.dump({"offers": merged}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {MERGED_PATH} ({len(merged)} offers) -- gitignored, local only")

if __name__ == "__main__":
    main()
