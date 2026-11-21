# China Country Dashboard (FINC 470)

Question: does the data point to RMB depreciation pressure, and what does it mean for a US firm with RMB cash flows?

| File | Purpose |
|---|---|
| `fetch_data.py` | Downloads 10 series (FRED, BIS, IMF), computes CPI YoY, writes `data.json`, appends `refresh_log.csv` |
| `verify.py` | Sanity checks + spot-checks against original sources (`verification_reference.json`) -> `VERIFICATION.md` |
| `build_dashboard.py` | Builds `index.html` (self-contained) |
| `.github/workflows/refresh.yml` | Daily scheduled refresh (13:30 UTC) + manual "Run workflow" button |
| `raw_seed/` | Values retrieved on 21 Nov 2026, used for the first build and for offline testing |

## Setup (5 minutes)
1. Create a GitHub repo, upload this folder, push.
2. Settings > Pages > deploy from branch `main`, folder `/docs`. The dashboard URL appears there.
3. Actions tab > "Refresh China dashboard" > **Run workflow**. This is your demonstration: the run log and the new rows in `refresh_log.csv` are the evidence of a successful refresh. Screenshot both.
4. Without GitHub: `python fetch_data.py && python verify.py && python build_dashboard.py`, then open `index.html`. To schedule locally: `crontab -e` -> `30 13 * * * cd /path/to/china-dashboard && python3 fetch_data.py && python3 verify.py; python3 build_dashboard.py`.

## Refresh behavior
- "Last successful refresh" (top of the dashboard) is the time the fetch ran. Each chart separately lists its **latest observation** date. A refresh with no new source data is still a success.
- If a download fails the series keeps its old values, is marked STALE on the page, and `refresh_log.csv` records it.

## Status of testing (be upfront in your memo)
- The parsers, transformations, verification and HTML build were run end-to-end on the saved seed data.
- The live downloads in `fetch_data.py` could not be run from the build environment (no outbound access to the data sites), so **run it once on your computer or in GitHub Actions before submitting** and use that run as your refresh evidence. If a source changed its response format, the series will show STALE rather than break the page.
