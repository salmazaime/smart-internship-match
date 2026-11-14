import csv, json, os, time

# ---------------------------------------------------------------------------
# My match KPI (CM1 + CM2): exclude what is infeasible, THEN compare the rest.
#
# Step 1 - feasibility filter. An offer is excluded (score 0, never ranked)
#   if it cannot be my end-of-studies internship:
#     - duration known and shorter than MIN_DURATION_MONTHS (my PFE needs 6 months)
#     - required level clearly below an engineering school final year (BUT, Bac+2)
# Step 2 - for feasible offers:
#     coverage = required skills I have / required skills
#     score    = sum(my level / 5 for matched skills) / required skills
#   A skill held at level 5 counts 1, at level 3 counts 0.6, missing counts 0.
# Skill names are compared after normalization (case, spaces, a few true synonyms),
# because the AI extraction does not always spell a skill the same way.
# ---------------------------------------------------------------------------
MAX_LEVEL = 5
MIN_DURATION_MONTHS = 6
LEVEL_TOO_LOW = ("but", "bac+2", "bac + 2", "dut", "bts")

SYNONYMS = {
    "oauth2": "oauth 2.0 / oidc / saml",
    "openid connect": "oauth 2.0 / oidc / saml",
    "saml 2.0": "oauth 2.0 / oidc / saml",
    "entra id": "microsoft entra id",
    "azure ad": "microsoft entra id",
    "identity and access management": "iam",
    "anglais": "english",
    "iso/iec 27001": "iso 27001",
    "regulatory compliance": "compliance automation",
}


def norm(s):
    k = " ".join(str(s).lower().split())
    return SYNONYMS.get(k, k)


def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = {"level": int(row["level"]), "evidence": row["evidence"]}
    return profile


def feasibility(offer):
    """Return (feasible, reason). Unknown information never excludes an offer."""
    d = offer.get("duration_months")
    if d is not None and d < MIN_DURATION_MONTHS:
        return False, f"duration {d} months < {MIN_DURATION_MONTHS} required for my PFE"
    lvl = (offer.get("experience_required") or "").lower()
    if any(w in lvl.split() or w in lvl for w in LEVEL_TOO_LOW):
        return False, f"targets another study level ({offer.get('experience_required')})"
    return True, "feasible"


def score_offer(profile, required_skills):
    req, seen = [], set()
    for s in required_skills or []:
        if norm(s) not in seen:
            seen.add(norm(s))
            req.append(s)
    if not req:
        return {"score": 0.0, "coverage": 0.0, "matched": [], "gaps": []}
    by_key = {norm(name): name for name in profile}
    matched, gaps, weight = [], [], 0.0
    for s in req:
        name = by_key.get(norm(s))
        if name:
            matched.append(name)            # MY skill name -> draft_cv.py finds the evidence
            weight += profile[name]["level"] / MAX_LEVEL
        else:
            gaps.append(s)
    return {"score": round(weight / len(req), 3),
            "coverage": round(len(matched) / len(req), 3),
            "matched": matched, "gaps": gaps}


def build_output(results, profile):
    feasible = [r for r in results if r["feasible"]]
    gap_counts, matched_counts = {}, {}
    for r in feasible:
        for g in r["gaps"]:
            gap_counts[g] = gap_counts.get(g, 0) + 1
        for s in r["matched"]:
            matched_counts[s] = matched_counts.get(s, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_matched = sorted(matched_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_offers": len(results),
        "n_feasible": len(feasible),
        "offers_per_source": {s: sum(1 for r in results if r["source"] == s) for s in {r["source"] for r in results}},
        "offers": results,
        "top_skill_gaps": [{"skill": s, "count": c} for s, c in top_gaps],
        "top_matched_skills": [{"skill": s, "count": c, "level": profile[s]["level"]} for s, c in top_matched],
        "n_offers_with_compensation": sum(1 for r in results if r.get("compensation_mentioned")),
    }


# Scraped offers (publishable: false) are published only as my own analysis:
# no title, company, place, link or description ever reaches the public repo.
IDENTIFYING = ("title", "company", "location", "url", "responsibilities", "experience_required",
               "compensation_mentioned", "date_posted", "constraint")


def anonymize(r, i):
    out = {k: v for k, v in r.items() if k not in IDENTIFYING}
    out["id"] = f"offer_{i:02d}"
    out["title"] = f"Offre {r['source']} n°{i}"
    out["has_compensation"] = bool(r.get("compensation_mentioned"))
    return out


def main():
    profile = load_profile()
    with open("data/offers/structured_offers.json", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for offer in data["offers"]:
        ok, why = feasibility(offer)
        m = score_offer(profile, offer["required_skills"])
        if not ok:
            m["score"] = 0.0
        results.append({**offer, **m, "feasible": ok, "feasibility_reason": why})

    results.sort(key=lambda r: (r["feasible"], r["score"]), reverse=True)
    for r in results:
        flag = "" if r["feasible"] else f"  [EXCLUDED: {r['feasibility_reason']}]"
        print(f"  {r['score']:.3f}  {r['title']} @ {r['company']}  (coverage {r['coverage']:.0%}, gaps: {r['gaps']}){flag}")

    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/matches_all_local.json", "w", encoding="utf-8") as f:
        json.dump(build_output(results, profile), f, indent=2, ensure_ascii=False)
    print(f"Wrote data/offers/matches_all_local.json ({len(results)} offers) -- gitignored, local only")

    public = [r if r.get("publishable") else anonymize(r, i) for i, r in enumerate(results, 1)]
    out = build_output(public, profile)
    out["n_offers_with_compensation"] = sum(1 for r in results if r.get("compensation_mentioned"))
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/matches.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("Wrote docs/data/matches.json (scraped offers anonymized: scores only)")


if __name__ == "__main__":
    main()
