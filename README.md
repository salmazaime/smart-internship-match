# Smart Internship Match

Personal decision-support pipeline for my internship search: fetch real offers (France Travail API), structure them with a local LLM (Ollama), match them against my own skills, draft grounded cover-letter openings, and show the result on a dashboard.

Cloud: `scripts/fetch_offers.py` (weekly GitHub Action). Local: merge, extract, match, draft. Only `docs/data/matches.json` (official data only) is ever published.
