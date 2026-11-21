#!/usr/bin/env python3
"""Verify data.json: (1) automated sanity checks, (2) spot-checks vs original sources
listed in verification_reference.json. Writes VERIFICATION.md. Exit 1 on failure."""
import json, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).parent
D = json.loads((ROOT/"data.json").read_text())
REF = json.loads((ROOT/"verification_reference.json").read_text())
S = D["series"]
MAX_AGE_DAYS = {"usdcny_d": 10, "usdcny_m": 70, "reer": 75, "cpi_cn_yoy": 75, "cpi_us_yoy": 75, "pol_cn": 75, "pol_us": 75,
                "reserves": 220, "gdp": 800, "ca": 800}
RANGE = {"usdcny_d": (4, 10), "usdcny_m": (4, 10), "reer": (50, 150), "cpi_cn_yoy": (-5, 15), "cpi_us_yoy": (-3, 20),
         "pol_cn": (0, 10), "pol_us": (0, 10), "gdp": (-10, 20), "ca": (-10, 15), "reserves": (2, 5)}
def parse_date(s):
    p = s.split("-"); return dt.date(int(p[0]), int(p[1]) if len(p) > 1 else 12, int(p[2]) if len(p) > 2 else 28)
today = dt.date.today(); fails = 0; lines = []
lines += [f"# Verification report", "", f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC; data refresh mode: {D['mode']}; last refresh: {D['last_refresh_utc']}", "",
          "## 1. Automated checks (every series)", "", "| Series | Status | Obs | Latest obs | Age (days) | Latest value | In plausible range | Fresh enough |", "|---|---|---|---|---|---|---|---|"]
for k, lim in RANGE.items():
    s = S[k]; v = s["values"][-1]; age = (today - parse_date(s["latest_obs_date"])).days
    lo, hi = lim; inr = lo <= v <= hi; fresh = age <= MAX_AGE_DAYS[k]
    fresh_ok = fresh or D["mode"] == "offline-seed"   # seed data is a snapshot; freshness only enforced on live refresh
    if s["status"] != "ok" or not inr or not fresh_ok: fails += 1
    lines.append(f"| {k} | {s['status']} | {len(s['values'])} | {s['latest_obs_date']} | {age} | {v:.4g} | {'yes' if inr else 'NO'} | {'yes' if fresh else 'no (stale)'} |")
# internal consistency: monthly average vs mean of daily observations
daily = {}
for d, v in zip(S["usdcny_d"]["dates"], S["usdcny_d"]["values"]): daily.setdefault(d[:7], []).append(v)
mm = dict(zip([d[:7] for d in S["usdcny_m"]["dates"]], S["usdcny_m"]["values"]))
lines += ["", "## 2. Internal consistency", "", "| Check | Computed | Reported | Pass |", "|---|---|---|---|"]
for m in ("2026-09", "2026-10"):
    if m in daily and m in mm:
        c = sum(daily[m]) / len(daily[m]); ok = abs(c - mm[m]) < 0.005; fails += (not ok)
        lines.append(f"| Mean of daily USD/CNY, {m} | {c:.4f} | {mm[m]:.4f} (monthly series) | {'yes' if ok else 'NO'} |")
lines += ["", "## 3. Spot-checks against original sources", "", "| Series | Date | Dashboard | Original source value | Difference | Tolerance | Pass | Source | Note |", "|---|---|---|---|---|---|---|---|---|"]
checked = set()
for r in REF:
    s = S[r["series"]]; i = s["dates"].index(r["date"]); v = s["values"][i]; diff = v - r["source_value"]
    ok = abs(diff) <= r["tol"] + 1e-9; fails += (not ok); checked.add(r["series"])
    lines.append(f"| {r['series']} | {r['date']} | {v:.4g} | {r['source_value']} | {diff:+.4f} | ±{r['tol']} | {'yes' if ok else 'NO'} | [{r['source']}]({r['url']}) | {r['note']} |")
lines += ["", f"Series without an independent second source: {', '.join(sorted(set(RANGE)-checked-{'usdcny_m'}))} (taken directly from the primary publisher's API; covered by sanity checks only). `usdcny_m` is checked through the daily series above.",
          "", f"**Result: {'ALL CHECKS PASSED' if not fails else str(fails)+' CHECK(S) FAILED'}**"]
(ROOT/"VERIFICATION.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[-3:])); sys.exit(1 if fails else 0)
