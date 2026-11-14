"""Monitoring check (CM4) on my own search: trigger -> run -> check.

My definition of "something is wrong with my internship search":
  M1  a feasible offer in my top 3 is still "to_apply" more than 5 days later
  M2  an application has been "sent" for more than 14 days with no answer
  M3  fewer than 3 feasible offers left -> my keywords / sources are too narrow
Each run is appended to docs/data/monitoring.json (the history proves it ran).
"""
import csv, json, os, time
from datetime import date, datetime

TRACKER = "data/tracking/applications.csv"
MATCHES = "docs/data/matches.json"
HISTORY = "docs/data/monitoring.json"
ACT_WITHIN_DAYS, ANSWER_WITHIN_DAYS, MIN_FEASIBLE = 5, 14, 3
ANSWERED = ("interview", "rejected", "offer")


def age(d):
    try:
        return (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days
    except (TypeError, ValueError):
        return None


def main():
    with open(TRACKER, encoding="utf-8") as f:
        apps = list(csv.DictReader(f))
    with open(MATCHES, encoding="utf-8") as f:
        m = json.load(f)
    feasible = [o for o in m["offers"] if o.get("feasible")]
    top3 = {o["id"] for o in feasible[:3]}

    alerts = []
    for a in apps:
        st = a["status"].strip()
        if st == "to_apply" and a["offer_id"] in top3 and (age(a["last_update"]) or 0) > ACT_WITHIN_DAYS:
            alerts.append(f"M1 {a['offer_id']}: top-3 offer not applied after {age(a['last_update'])} days")
        if st == "sent" and (age(a["date_sent"]) or 0) > ANSWER_WITHIN_DAYS:
            alerts.append(f"M2 {a['offer_id']}: no answer {age(a['date_sent'])} days after sending -> follow up")
    if len(feasible) < MIN_FEASIBLE:
        alerts.append(f"M3 only {len(feasible)} feasible offers -> broaden search")

    sent = [a for a in apps if a["status"] in ("sent",) + ANSWERED]
    answered = [a for a in apps if a["status"] in ANSWERED]
    run = {"run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
           "tracked": len(apps), "applications_sent": len(sent),
           "response_rate_pct": round(100 * len(answered) / len(sent), 1) if sent else None,
           "feasible_offers": len(feasible), "alerts": alerts,
           "status": "ALERT" if alerts else "OK"}

    hist = {"runs": []}
    if os.path.exists(HISTORY):
        with open(HISTORY, encoding="utf-8") as f:
            hist = json.load(f)
    hist["runs"].append(run)
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)
    print(f"Run #{len(hist['runs'])}: {run['status']} ({len(sent)} sent, {len(feasible)} feasible offers)")
    for a in alerts:
        print("  ALERT", a)


if __name__ == "__main__":
    main()
