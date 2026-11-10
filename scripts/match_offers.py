import csv, json, os, re, time

def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = {"level": int(row["level"]), "evidence": row["evidence"]}
    return profile

# ---------------------------------------------------------------------------
# MATCH KPI (my design)
#
# Question the KPI answers: "how well does this offer fit what I can already do?"
#
# 1. Matching. A skill counts as matched if, after normalizing, it equals one of
#    my profile skills. normalize() lowercases and strips spaces, dots, hyphens
#    and slashes, so "Power BI", "power bi" and "PowerBI" are the same skill, and
#    "Computer vision" / "computer vision" never split into two skills. ALIASES
#    covers common alternative names; add your own as you see them in real data.
#
# 2. coverage = matched skills / required skills. "What share of this offer's
#    requirements do I cover?" This is what draft_cv.py filters on.
#
# 3. score = sum(level/5 for each matched skill) / (n_required + 1)
#    - a matched skill counts more when my level is higher (level 4 = 0.8, level 2 = 0.4)
#    - the +1 in the denominator is a small penalty for thin evidence: without it,
#      an offer listing a single skill I know would score the same as an offer
#      listing six where I cover all six. With it, 1 of 1 ranks below 5 of 6.
#    - an offer with no extracted skills scores 0 (nothing to match is not a match).
#
# Limit to remember in the report: this only sees skills the AI extracted, and a
# skill missing from the offer text is invisible. It measures fit to the stated
# requirements, not the quality of the internship.
# ---------------------------------------------------------------------------
ALIASES = {
    "postgres": "postgresql",
    "js": "javascript",
    "pbi": "powerbi",
    "restapi": "apirest",
    "apirestful": "apirest",
    "restfulapi": "apirest",
    "gitgithub": "git",
    "github": "git",
    "gitlab": "git",
    "sklearn": "scikitlearn",
    "ml": "machinelearning",
}

def normalize(skill):
    key = re.sub(r"[\s\.\-_/]+", "", str(skill).lower())
    return ALIASES.get(key, key)

def score_offer(profile, required_skills):
    my_skills = {normalize(name): (name, info["level"]) for name, info in profile.items()}

    matched, gaps, level_points = [], [], 0.0
    seen = set()
    for skill in required_skills or []:
        key = normalize(skill)
        if not key or key in seen:  # ignore blanks and duplicates within one offer
            continue
        seen.add(key)
        if key in my_skills:
            profile_name, level = my_skills[key]
            matched.append(profile_name)  # profile spelling, so draft_cv can find the evidence
            level_points += level / 5
        else:
            gaps.append(skill)

    n_required = len(seen)
    if n_required == 0:
        return {"score": 0.0, "coverage": 0.0, "matched": [], "gaps": []}

    return {
        "score": round(level_points / (n_required + 1), 3),
        "coverage": round(len(matched) / n_required, 3),
        "matched": matched,
        "gaps": gaps,
    }

def build_output(results, profile):
    gap_counts = {}
    matched_counts = {}
    for r in results:
        for g in r["gaps"]:
            gap_counts[g] = gap_counts.get(g, 0) + 1
        for s in r["matched"]:
            matched_counts[s] = matched_counts.get(s, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_matched = sorted(matched_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    n_with_comp = sum(1 for r in results if r.get("compensation_mentioned"))
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_offers": len(results),
        "offers": results,
        "top_skill_gaps": [{"skill": s, "count": c} for s, c in top_gaps],
        "top_matched_skills": [{"skill": s, "count": c, "level": profile[s]["level"]} for s, c in top_matched],
        "n_offers_with_compensation": n_with_comp,
    }

def main():
    profile = load_profile()
    with open("data/offers/structured_offers.json") as f:
        data = json.load(f)

    results = []
    for offer in data["offers"]:
        m = score_offer(profile, offer["required_skills"])
        results.append({**offer, **m})

    results.sort(key=lambda r: r["score"], reverse=True)
    for r in results:
        print(f"  {r['score']:.3f}  {r['title']} @ {r['company']}  ({r['source']}, "
              f"coverage {r['coverage']:.0%}, gaps: {r['gaps']})")

    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/matches_all_local.json", "w") as f:
        json.dump(build_output(results, profile), f, indent=2, ensure_ascii=False)
    print(f"Wrote data/offers/matches_all_local.json ({len(results)} offers) -- gitignored, local only")

    public_results = [r for r in results if r.get("publishable", False)]
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/matches.json", "w") as f:
        json.dump(build_output(public_results, profile), f, indent=2, ensure_ascii=False)
    print(f"Wrote docs/data/matches.json ({len(public_results)} of {len(results)} offers -- publishable sources only)")

if __name__ == "__main__":
    main()
