import json, os, time
import pandas as pd
from jobspy import scrape_jobs

# Local-only, on-demand scraper (never run in GitHub Actions). Indeed and
# ZipRecruiter only: LinkedIn and Google are deliberately excluded (higher ToS
# enforcement risk). Output is gitignored and never published.

SITES = ["indeed", "zip_recruiter"]
SEARCH_TERM = "stage informatique"
LOCATION = "France"
RESULTS_WANTED = 30
HOURS_OLD = 336  # 14 days

def safe(row, key, default=None):
    # pandas NaN is truthy, so `row.get(key) or default` would return NaN itself.
    v = row.get(key)
    return v if pd.notna(v) else default

def main():
    print(f"Scraping {SITES} for '{SEARCH_TERM}' in {LOCATION}...")
    jobs = scrape_jobs(
        site_name=SITES,
        search_term=SEARCH_TERM,
        location=LOCATION,
        results_wanted=RESULTS_WANTED,
        hours_old=HOURS_OLD,
        country_indeed=LOCATION,
    )
    print(f"Found {len(jobs)} raw results")

    interns = jobs[jobs["job_type"].fillna("").str.contains("internship", case=False)]
    print(f"{len(interns)} of those are tagged job_type=internship")

    offers = []
    for _, row in interns.iterrows():
        offers.append({
            "id": f"jobspy_{safe(row, 'id')}",
            "source": safe(row, "site"),
            "title": safe(row, "title"),
            "company": safe(row, "company"),
            "location": safe(row, "location"),
            "description": safe(row, "description", ""),
            "url": safe(row, "job_url"),
            "date_posted": str(safe(row, "date_posted")) if safe(row, "date_posted") else None,
        })

    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/jobspy_offers.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "offers": offers}, f, indent=2, ensure_ascii=False)
    print(f"Wrote data/offers/jobspy_offers.json ({len(offers)} offers) -- gitignored, local only")

if __name__ == "__main__":
    main()
