#!/usr/bin/env python3
"""Fetch China dashboard data from primary/official sources and write data.json.

Usage:
  python fetch_data.py                 # live fetch (needs internet)
  python fetch_data.py --offline DIR   # parse saved raw responses from DIR/<key>.txt (testing)

Standard library only. If a series fails to download, the previous values are kept
and the series is marked "stale" so a failure is visible, never silent.
"""
import csv, io, json, sys, urllib.request, datetime as dt
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data.json"
LOG = ROOT / "refresh_log.csv"

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}&{q}"
BIS = "https://stats.bis.org/api/v2/data/dataflow/BIS/{flow}/1.0/{key}?{q}&format=csv"
IMF = "https://www.imf.org/external/datamapper/api/v1/{ind}/CHN"

# kind: fred | bis | imf ; every series documents units, frequency, source (shown on the dashboard)
SERIES = {
  "usdcny_m": dict(kind="fred", url=FRED.format(id="DEXCHUS", q="cosd=2022-01-01&fq=Monthly&fam=avg"), col="DEXCHUS",
      title="USD/CNY exchange rate (monthly average)", units="CNY per 1 USD (class convention: CNY/USD; up = RMB weaker)",
      freq="Monthly (average of daily)", source="Federal Reserve Board H.10 via FRED (DEXCHUS)"),
  "usdcny_d": dict(kind="fred", url=FRED.format(id="DEXCHUS", q="cosd=2026-08-15"), col="DEXCHUS",
      title="USD/CNY exchange rate (daily)", units="CNY per 1 USD", freq="Daily (noon NY buying rates)",
      source="Federal Reserve Board H.10 via FRED (DEXCHUS)"),
  "reer": dict(kind="bis", url=BIS.format(flow="WS_EER", key="M.R.B.CN", q="startPeriod=2023-01"), 
      title="Real broad effective exchange rate, China", units="Index (BIS base year; up = RMB real appreciation)",
      freq="Monthly", source="Bank for International Settlements, WS_EER (M.R.B.CN)"),
  "cpi_cn_idx": dict(kind="bis", url=BIS.format(flow="WS_LONG_CPI", key="M.CN.628", q="startPeriod=2024-01"),
      title="China CPI index (input to YoY)", units="Index", freq="Monthly", source="BIS WS_LONG_CPI (M.CN.628), from NBS"),
  "cpi_us_idx": dict(kind="fred", url=FRED.format(id="CPIAUCSL", q="cosd=2024-01-01"), col="CPIAUCSL",
      title="US CPI-U index, seasonally adjusted (input to YoY)", units="Index 1982-84=100", freq="Monthly",
      source="US BLS via FRED (CPIAUCSL)"),
  "pol_cn": dict(kind="bis", url=BIS.format(flow="WS_CBPOL", key="M.CN", q="startPeriod=2022-01"),
      title="China policy rate (1-year Loan Prime Rate)", units="Percent per year", freq="Monthly (end of period)",
      source="BIS WS_CBPOL (M.CN), from PBoC"),
  "pol_us": dict(kind="bis", url=BIS.format(flow="WS_CBPOL", key="M.US", q="startPeriod=2022-01"),
      title="US policy rate (fed funds target midpoint)", units="Percent per year", freq="Monthly (end of period)",
      source="BIS WS_CBPOL (M.US), from the Federal Reserve"),
  "gdp": dict(kind="imf", url=IMF.format(ind="NGDP_RPCH"), imf="NGDP_RPCH", from_year=2015, to_year=2028, proj_from=2026,
      title="Real GDP growth", units="Percent, year over year", freq="Annual",
      source="IMF World Economic Outlook (DataMapper NGDP_RPCH); 2026+ are IMF projections"),
  "ca": dict(kind="imf", url=IMF.format(ind="BCA_NGDPD"), imf="BCA_NGDPD", from_year=2015, to_year=2028, proj_from=2026,
      title="Current account balance", units="Percent of GDP (positive = surplus)", freq="Annual",
      source="IMF World Economic Outlook (DataMapper BCA_NGDPD); 2026+ are IMF projections"),
  "reserves": dict(kind="fred", url=FRED.format(id="TRESEGCNM052N", q="cosd=2022-01-01"), col="TRESEGCNM052N", scale=1e-6,
      title="Total reserves excluding gold", units="USD trillions", freq="Monthly (published with a lag)",
      source="IMF International Financial Statistics via FRED (TRESEGCNM052N)"),
}

def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "china-dashboard/1.0 (student project)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def month_key(s):  # '2026-09' or '2026-09-01' -> '2026-09'
    return s[:7]

def parse(spec, text):
    """Return (dates, values) with missing observations dropped."""
    d, v = [], []
    if spec["kind"] == "fred":
        for row in csv.DictReader(io.StringIO(text)):
            val = row[spec["col"]].strip()
            if val and val != ".":
                d.append(row["observation_date"]); v.append(float(val) * spec.get("scale", 1))
    elif spec["kind"] == "bis":
        for row in csv.DictReader(io.StringIO(text)):
            if row.get("OBS_VALUE", "").strip():
                d.append(row["TIME_PERIOD"]); v.append(float(row["OBS_VALUE"]))
    elif spec["kind"] == "imf":
        vals = json.loads(text)["values"][spec["imf"]]["CHN"]
        for y in range(spec["from_year"], spec["to_year"] + 1):
            if str(y) in vals:
                d.append(str(y)); v.append(float(vals[str(y)]))
    if not d:
        raise ValueError("no observations parsed")
    return d, v

def yoy(dates, vals):
    """YoY % change from a monthly index; skips months whose year-ago value is missing."""
    idx = {month_key(a): b for a, b in zip(dates, vals)}
    od, ov = [], []
    for k in sorted(idx):
        y, m = k.split("-"); prev = f"{int(y)-1}-{m}"
        if prev in idx:
            od.append(k); ov.append(round((idx[k] / idx[prev] - 1) * 100, 2))
    return od, ov

def main():
    offline = Path(sys.argv[sys.argv.index("--offline") + 1]) if "--offline" in sys.argv else None
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    old = json.loads(DATA.read_text())["series"] if DATA.exists() else {}
    out, log, failures = {}, [], 0
    for key, spec in SERIES.items():
        meta = {k: spec[k] for k in ("title", "units", "freq", "source", "url")}
        try:
            text = (offline / f"{key}.txt").read_text() if offline else download(spec["url"])
            dates, vals = parse(spec, text)
            meta.update(dates=dates, values=vals, status="ok", fetched_utc=now.isoformat())
        except Exception as e:  # keep last good data, flag as stale
            failures += 1
            meta.update(old.get(key, {"dates": [], "values": []}))
            meta.update(status="stale", error=str(e)[:200])
        if "proj_from" in spec: meta["proj_from"] = spec["proj_from"]
        meta["latest_obs_date"] = meta["dates"][-1] if meta["dates"] else None
        out[key] = meta
        log.append([now.isoformat(), "offline-seed" if offline else "live", key, meta["status"], len(meta["dates"]),
                    meta["latest_obs_date"], meta["values"][-1] if meta["values"] else ""])
    # derived inflation series
    for k, src in (("cpi_cn_yoy", "cpi_cn_idx"), ("cpi_us_yoy", "cpi_us_idx")):
        s = out[src]; d, v = yoy(s["dates"], s["values"])
        out[k] = dict(title=s["title"].replace("index (input to YoY)", "inflation").replace("CPI-U index, seasonally adjusted (input to YoY)", "CPI-U inflation"),
                      units="Percent, year over year (computed: index / index 12 months earlier - 1)", freq="Monthly",
                      source=s["source"], url=s["url"], dates=d, values=v, status=s["status"], latest_obs_date=d[-1] if d else None)
    ok = sum(1 for s in SERIES if out[s]["status"] == "ok")
    # refresh time is stored separately from latest observation dates (assignment requirement)
    payload = dict(last_refresh_utc=now.isoformat() if ok else (json.loads(DATA.read_text()).get("last_refresh_utc") if DATA.exists() else None),
                   mode="offline-seed" if offline else "live", series_ok=ok, series_total=len(SERIES), series=out)
    DATA.write_text(json.dumps(payload, indent=1))
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["refresh_utc", "mode", "series", "status", "n_obs", "latest_obs_date", "latest_value"])
        w.writerows(log)
    print(f"{now.isoformat()}  refreshed {ok}/{len(SERIES)} series ({payload['mode']})")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
