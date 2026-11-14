name: Fetch internship offers

"on":
  workflow_dispatch: {}
  schedule:
    - cron: "0 7 * * 1"

permissions:
  contents: write

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - run: pip install requests
      # France Travail "Offres d'emploi v2" is no longer offered to new applications:
      # the step is kept so it works again when the API is available, but never blocks.
      - name: Fetch France Travail offers
        continue-on-error: true
        run: python scripts/fetch_offers.py
        env:
          FRANCETRAVAIL_CLIENT_ID: ${{ secrets.FRANCETRAVAIL_CLIENT_ID }}
          FRANCETRAVAIL_CLIENT_SECRET: ${{ secrets.FRANCETRAVAIL_CLIENT_SECRET }}
      - name: Commit updated offers
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          if [ -f data/offers/raw_offers.json ]; then git add data/offers/raw_offers.json; fi
          git commit -m "Fetch latest offers [automated]" || echo "Nothing to commit"
          git push
