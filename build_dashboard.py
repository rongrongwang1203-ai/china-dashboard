#!/usr/bin/env python3
"""Build index.html (self-contained, no external libraries) from data/data.json."""
import json, math, html, datetime as dt
from pathlib import Path
ROOT = Path(__file__).parent
D = json.loads((ROOT/"data.json").read_text()); S = D["series"]

def mnum(d):                       # '2026-09' / '2026-09-01' -> month number
    p = d.split("-"); return int(p[0])*12 + int(p[1]) - 1
def dnum(d):
    return dt.date.fromisoformat(d).toordinal()
def nice(lo, hi, n=5):
    span = hi - lo or 1; step = 10**math.floor(math.log10(span/n)); 
    for m in (1, 2, 2.5, 5, 10):
        if span/(step*m) <= n: step *= m; break
    a = math.floor(lo/step)*step; b = math.ceil(hi/step)*step
    return a, b, step
def fmt(v, dec): return f"{v:,.{dec}f}"

def chart(cid, series, dec=2, kind="line", xmode="month", zero=False, pad=True):
    """series: list of dict(name, dates, values, cls, proj_from(optional)). Returns svg+legend+table html."""
    W, H, L, R, T, B = 640, 280, 52, 14, 12, 30
    xf = {"month": mnum, "day": dnum, "year": lambda d: int(d)}[xmode]
    xs_all = sorted({xf(d) for s in series for d in s["dates"]})
    x0, x1 = xs_all[0], xs_all[-1]
    ys = [v for s in series for v in s["values"]]
    lo, hi = min(ys + ([0] if zero or kind == "bar" else [])), max(ys + ([0] if kind == "bar" else []))
    if pad and kind == "line" and not zero: m = (hi-lo)*0.08; lo, hi = lo-m, hi+m
    a, b, step = nice(lo, hi)
    px = lambda x: L + (x-x0)/(x1-x0 or 1)*(W-L-R) if kind == "line" else L + (xs_all.index(x)+0.5)/len(xs_all)*(W-L-R)
    py = lambda y: T + (b-y)/(b-a)*(H-T-B)
    g = [f'<line class="grid" x1="{L}" x2="{W-R}" y1="{py(a+i*step):.1f}" y2="{py(a+i*step):.1f}"/>'
         f'<text class="tick" x="{L-6}" y="{py(a+i*step)+4:.1f}" text-anchor="end">{fmt(a+i*step, 0 if step>=1 else 1 if step>=0.1 else 2)}</text>'
         for i in range(int(round((b-a)/step))+1)]
    if a < 0 < b: g.append(f'<line class="zero" x1="{L}" x2="{W-R}" y1="{py(0):.1f}" y2="{py(0):.1f}"/>')
    # x ticks
    if xmode == "month":
        for yr in range(x0//12, x1//12+1):
            if x0 <= yr*12 <= x1: g.append(f'<text class="tick" x="{px(yr*12):.1f}" y="{H-8}" text-anchor="middle">{yr}</text>')
    elif xmode == "year":
        for i, x in enumerate(xs_all):
            if i % 2 == 0: g.append(f'<text class="tick" x="{px(x):.1f}" y="{H-8}" text-anchor="middle">{x}</text>')
    else:
        step_d = max(1, len(xs_all)//5)
        for x in xs_all[::step_d]:
            g.append(f'<text class="tick" x="{px(x):.1f}" y="{H-8}" text-anchor="middle">{dt.date.fromordinal(x).strftime("%d %b")}</text>')
    marks, pts, labels = [], [], []
    bw = (W-L-R)/len(xs_all)*0.62/len(series) if kind == "bar" else 0
    for si, s in enumerate(series):
        xy = [(xf(d), v, d) for d, v in zip(s["dates"], s["values"])]
        if kind == "line":
            path = " ".join(("M" if i == 0 else "L") + f"{px(x):.1f},{py(v):.1f}" for i, (x, v, _) in enumerate(xy))
            marks.append(f'<path class="line {s["cls"]}" d="{path}"/>')
            x, v, d = xy[-1]; marks.append(f'<circle class="dot {s["cls"]}" cx="{px(x):.1f}" cy="{py(v):.1f}" r="4"/>')
            if len(series) <= 4: labels.append(f'<text class="lab" x="{px(x)-6:.1f}" y="{py(v)-12:.1f}" text-anchor="end">{fmt(v, dec)}</text>')
        else:
            for x, v, d in xy:
                proj = s.get("proj_from") and int(d) >= s["proj_from"]
                y1 = min(py(0), py(v)); y0 = max(py(0), py(v))
                cx = px(x) - bw/2 + si*bw
                marks.append(f'<rect class="bar {s["cls"]}{" proj" if proj else ""}" x="{cx:.1f}" y="{y1:.1f}" width="{bw*1.0:.1f}" height="{max(y0-y1,1):.1f}" rx="3"/>')
        for x, v, d in xy:
            pts.append(dict(x=round(px(x), 1), y=round(py(v), 1), d=d, v=round(v, 4), s=s["name"], c=s["cls"],
                            p=bool(s.get("proj_from") and xmode == "year" and int(d) >= s["proj_from"])))
    legend = "".join(f'<span class="lg"><i class="sw {s["cls"]}"></i>{html.escape(s["name"])}</span>' for s in series) if len(series) > 1 else ""
    # table view: latest 14 rows
    dates = sorted({d for s in series for d in s["dates"]})[-14:]
    lookup = [dict(zip(s["dates"], s["values"])) for s in series]
    rows = "".join("<tr><td>%s</td>%s</tr>" % (d, "".join(f"<td>{fmt(l[d], dec) if d in l else '–'}</td>" for l in lookup)) for d in reversed(dates))
    head = "<th>Date</th>" + "".join(f"<th>{html.escape(s['name'])}</th>" for s in series)
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(" vs ".join(s["name"] for s in series))} chart" class="plot" data-id="{cid}">'
           + "".join(g) + "".join(marks) + "".join(labels) +
           f'<line class="xh" x1="0" x2="0" y1="{T}" y2="{H-B}" visibility="hidden"/></svg>')
    return legend, svg, f'<details><summary>Table view (latest {len(dates)} observations)</summary><table>{"<tr>"+head+"</tr>"}{rows}</table></details>', pts

def card(cid, title, series_keys, spec, caption_series=None, note="", **kw):
    ser = []
    for name, key, cls in series_keys:
        s = S[key]; ser.append(dict(name=name, dates=s["dates"], values=s["values"], cls=cls, proj_from=s.get("proj_from")))
    legend, svg, table, pts = chart(cid, ser, **kw)
    cap = ""
    for key in (caption_series or [k for _, k, _ in series_keys]):
        s = S[key]
        cap += (f'<li><b>{html.escape(s["title"])}</b> — units: {html.escape(s["units"])}; frequency: {html.escape(s["freq"])}; '
                f'source: <a href="{html.escape(s["url"])}">{html.escape(s["source"])}</a>; <b>latest observation: {s["latest_obs_date"]}</b>'
                f'{" · <span class=bad>STALE (last refresh failed)</span>" if s["status"]!="ok" else ""}</li>')
    return (f'<section class="card"><h2>{title}</h2><p class="q">{spec}</p><div class="legend">{legend}</div>{svg}'
            f'<ul class="meta">{cap}</ul>{"<p class=note>"+note+"</p>" if note else ""}{table}</section>', {cid: pts})

# ------------ derived numbers for the narrative --------------------------------------------------
last = lambda k: S[k]["values"][-1]
usd_d = S["usdcny_d"]; usd_m = S["usdcny_m"]
m = dict(zip([d[:7] for d in usd_m["dates"]], usd_m["values"]))
jan25 = m["2025-01"]; oct26 = m["2026-10"]; appr = (jan25/oct26-1)*100
reer = dict(zip(S["reer"]["dates"], S["reer"]["values"]))
trough_k = min(reer, key=reer.get); reer_now = last("reer")
bench = [v for k, v in reer.items() if k < "2025-03"]; bench_avg = sum(bench)/len(bench)
cn_inf, us_inf = last("cpi_cn_yoy"), last("cpi_us_yoy")
ppp = ((1+us_inf/100)/(1+cn_inf/100)-1)*100         # relative PPP: implied RMB appreciation per year
gap = last("pol_cn") - last("pol_us")
gdp = dict(zip(S["gdp"]["dates"], S["gdp"]["values"])); ca = dict(zip(S["ca"]["dates"], S["ca"]["values"]))
res = dict(zip([d[:7] for d in S["reserves"]["dates"]], S["reserves"]["values"]))
res_chg = (S["reserves"]["values"][-1]/res["2024-12"]-1)*100

cards, ptsall = [], {}
def add(c): cards.append(c[0]); ptsall.update(c[1])
add(card("fx_m", "1 · RMB per US dollar", [("USD/CNY, monthly average", "usdcny_m", "s1")],
   "Is the RMB strengthening or weakening against the dollar? (Quote: CNY per USD, so a falling line = RMB appreciation)", dec=2))
add(card("fx_d", "1b · RMB per US dollar, daily", [("USD/CNY, daily", "usdcny_d", "s1")],
   "What has the spot rate done in the last ~10 weeks? (US holidays are gaps)", dec=4, xmode="day"))
add(card("reer", "2 · Real effective exchange rate", [("RMB real broad effective rate", "reer", "s1")],
   "Adjusting for inflation and trade weights, is the RMB expensive or cheap? (higher = real appreciation)", dec=1,
   note=f"Real index is {reer_now:.1f}; trough {reer[trough_k]:.1f} in {trough_k}; average Nov-2023–Feb-2025 was {bench_avg:.1f}. Benchmark window is short; class suggests a 30-year average."))
add(card("cpi", "3 · Inflation: China vs US", [("China CPI, % YoY", "cpi_cn_yoy", "s1"), ("US CPI, % YoY", "cpi_us_yoy", "s2")],
   "Relative PPP: the lower-inflation currency should appreciate", dec=1, zero=True,
   note="YoY = index ÷ index 12 months earlier − 1 (transformation done in fetch_data.py). US Oct-2025 index is missing in the source, so Oct-2026 YoY is not computable."))
add(card("pol", "4 · Policy interest rates", [("China 1-yr LPR", "pol_cn", "s1"), ("US fed funds (midpoint)", "pol_us", "s2")],
   "Does the interest-rate differential favor holding RMB?", dec=2, zero=True))
add(card("gdp", "5 · Real GDP growth", [("China real GDP growth", "gdp", "s1")],
   "Is growth supporting the currency? (hatched = IMF projection)", dec=1, kind="bar", xmode="year"))
add(card("ca", "6 · Current account balance", [("China current account, % of GDP", "ca", "s1")],
   "Is China a net supplier of foreign currency? (hatched = IMF projection)", dec=1, kind="bar", xmode="year"))
add(card("res", "7 · Foreign reserves", [("Total reserves excl. gold", "reserves", "s1")],
   "Does the central bank have ammunition to defend the currency?", dec=2,
   note="IMF definition includes SDRs and the IMF reserve position, so it runs about USD 0.07tn above SAFE's headline 'FX reserves' (verified, see below)."))

refresh = D["last_refresh_utc"]; age = ""
banner = ""
if D["mode"] == "offline-seed":
    banner = '<p class="warn"><b>Seed snapshot.</b> This copy was built from values retrieved on 21 Nov 2026 and saved in the .txt seed files. Run <code>python fetch_data.py</code> (or let the scheduled workflow run) to switch to live fetches.</p>'
stale = [k for k in ("usdcny_m","usdcny_d","reer","cpi_cn_idx","cpi_us_idx","pol_cn","pol_us","gdp","ca","reserves") if S[k]["status"] != "ok"]
status = f'{D["series_ok"]}/{D["series_total"]} series refreshed OK' + (f' · stale: {", ".join(stale)}' if stale else "")
kpis = [("USD/CNY (daily)", f'{last("usdcny_d"):.4f}', f'CNY per USD · {S["usdcny_d"]["latest_obs_date"]}'),
        ("RMB vs Jan 2025", f'+{appr:.1f}%', "monthly avg 7.30 → 6.68 (appreciation)"),
        ("Real eff. rate", f'{reer_now:.1f}', f'BIS index · {S["reer"]["latest_obs_date"]}'),
        ("CPI gap (US − CN)", f'{us_inf-cn_inf:.1f} pp', f'{us_inf:.1f}% vs {cn_inf:.1f}% · {S["cpi_cn_yoy"]["latest_obs_date"]}'),
        ("Policy-rate gap (CN − US)", f'{gap:+.2f} pp', f'{last("pol_cn"):.2f}% vs {last("pol_us"):.3f}%'),
        ("Current account", f'{ca["2025"]:.1f}% GDP', f'2025; IMF projects {ca["2026"]:.1f}% in 2026')]
kpi_html = "".join(f'<div class="kpi"><div class="kl">{a}</div><div class="kv">{b}</div><div class="ks">{c}</div></div>' for a, b, c in kpis)

CSS = """
:root{color-scheme:light;--bg:#fcfcfb;--panel:#fff;--ink:#0b0b0b;--ink2:#52514e;--grid:#e6e5e1;--s1:#2a78d6;--s2:#eb6834;--warnbg:#fff4e0;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#1a1a19;--panel:#222221;--ink:#f0efec;--ink2:#c3c2b7;--grid:#3a3a38;--s1:#3987e5;--s2:#d95926;--warnbg:#3a2f1a;--bad:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 18px 60px}h1{font-size:26px;margin:0 0 4px}h2{font-size:16px;margin:0 0 2px}
.sub{color:var(--ink2);margin:0 0 14px}.q{color:var(--ink2);margin:0 0 8px;font-size:13.5px}
.status{display:flex;flex-wrap:wrap;gap:6px 24px;background:var(--panel);border:1px solid var(--grid);border-radius:10px;padding:10px 14px;margin:12px 0}
.status b{font-variant-numeric:tabular-nums}.warn{background:var(--warnbg);border-radius:8px;padding:8px 12px;font-size:13.5px}.bad{color:var(--bad);font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--grid);border-radius:10px;padding:10px 12px}.kl{font-size:12px;color:var(--ink2)}.kv{font-size:24px;font-weight:650;font-variant-numeric:tabular-nums}.ks{font-size:12px;color:var(--ink2)}
.answer{background:var(--panel);border:1px solid var(--grid);border-radius:10px;padding:14px 18px;margin:14px 0}.answer h2{font-size:17px;margin-bottom:6px}.answer li{margin:4px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:14px}@media(max-width:560px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:14px 16px;position:relative}
.plot{width:100%;height:auto;display:block;overflow:visible}.plot .grid{stroke:var(--grid);stroke-width:1}.plot .zero{stroke:var(--ink2);stroke-width:1}
.tick{fill:var(--ink2);font-size:11px}.lab{fill:var(--ink);font-size:12px;font-weight:600}
.line{fill:none;stroke-width:2;stroke-linejoin:round}.line.s1{stroke:var(--s1)}.line.s2{stroke:var(--s2)}
.dot{stroke:var(--panel);stroke-width:2}.dot.s1{fill:var(--s1)}.dot.s2{fill:var(--s2)}
.bar.s1{fill:var(--s1)}.bar.s2{fill:var(--s2)}.bar.proj{fill:url(#hatch);stroke:var(--s1);stroke-width:1.5}.xh{stroke:var(--ink2);stroke-dasharray:3 3}
.legend{display:flex;gap:16px;font-size:12.5px;margin-bottom:2px}.lg{display:inline-flex;align-items:center;gap:6px}.sw{width:12px;height:12px;border-radius:3px;display:inline-block}.sw.s1{background:var(--s1)}.sw.s2{background:var(--s2)}
.meta{font-size:11.5px;color:var(--ink2);padding-left:16px;margin:6px 0}.meta a{color:var(--ink2)}.note{font-size:12px;color:var(--ink2);margin:4px 0}
details{font-size:12.5px;margin-top:6px}summary{cursor:pointer;color:var(--ink2)}table{border-collapse:collapse;margin-top:6px;font-variant-numeric:tabular-nums}td,th{padding:2px 12px 2px 0;text-align:left;font-size:12px}th{color:var(--ink2)}
#tip{position:fixed;pointer-events:none;background:var(--panel);color:var(--ink);border:1px solid var(--grid);border-radius:8px;padding:6px 9px;font-size:12px;box-shadow:0 2px 8px #0003;display:none;z-index:9}
footer{color:var(--ink2);font-size:12.5px;margin-top:22px}code{background:var(--grid);padding:1px 5px;border-radius:4px}
"""
JS = """
const P=%s,tip=document.getElementById('tip');
document.querySelectorAll('svg.plot').forEach(svg=>{const pts=P[svg.dataset.id],xh=svg.querySelector('.xh');
 svg.addEventListener('mousemove',e=>{const r=svg.getBoundingClientRect(),k=640/r.width,x=(e.clientX-r.left)*k;
  let best=null,bd=1e9;pts.forEach(p=>{const d=Math.abs(p.x-x);if(d<bd){bd=d;best=p}});if(!best)return;
  const same=pts.filter(p=>p.d===best.d);xh.setAttribute('x1',best.x);xh.setAttribute('x2',best.x);xh.setAttribute('visibility','visible');
  tip.innerHTML='<b>'+best.d+(best.p?' (IMF projection)':'')+'</b><br>'+same.map(p=>p.s+': <b>'+p.v+'</b>').join('<br>');
  tip.style.display='block';tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+14)+'px'});
 svg.addEventListener('mouseleave',()=>{tip.style.display='none';xh.setAttribute('visibility','hidden')})});
"""
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>China Country Dashboard – RMB pressure monitor</title><style>{CSS}</style></head><body><main>
<svg width="0" height="0" style="position:absolute"><defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="none"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--s1)" stroke-width="2.5"/></pattern></defs></svg>
<h1>China · Is the RMB under depreciation pressure?</h1>
<p class="sub">Question: do China's exchange rate, prices, interest rates and external balance point to a weaker or stronger RMB over the next 1–2 years, and what does that mean for a US firm with RMB cash flows?</p>
<div class="status"><span>Last successful refresh: <b>{refresh.replace("T"," ").replace("+00:00"," UTC")}</b></span><span>{status}</span><span>Refresh mode: {D["mode"]}</span>
<span>The refresh time is separate from each series' <i>latest observation</i> date, listed under every chart.</span></div>{banner}
<div class="kpis">{kpi_html}</div>
<div class="answer"><h2>Reading the evidence</h2><ul>
<li><b>No depreciation pressure in the data.</b> The RMB has appreciated about {appr:.0f}% against the dollar since January 2025 (monthly average {jan25:.2f} → {oct26:.2f} CNY/USD), and the real effective rate has recovered from {reer[trough_k]:.1f} ({trough_k}) to {reer_now:.1f}, roughly its level before early 2025 ({bench_avg:.1f}).</li>
<li><b>Relative PPP points to further RMB strength.</b> With inflation of {cn_inf:.1f}% in China and {us_inf:.1f}% in the US, relative PPP implies the RMB should appreciate by about {ppp:.1f}% a year over the medium run (class: S<sub>t+1</sub>/S<sub>t</sub> = (1+π*)/(1+π)); it is a medium-run guide, not a one-year forecast.</li>
<li><b>External balance is supportive.</b> The current account surplus was {ca["2025"]:.1f}% of GDP in 2025 (IMF projects {ca["2026"]:.1f}% for 2026) and reserves are up {res_chg:.1f}% since December 2024.</li>
<li><b>Offsetting factors:</b> the 1-year LPR ({last("pol_cn"):.1f}%) is {abs(gap):.2f} pp below the US policy rate, so RMB is the cheaper funding currency, and IMF growth projections slow from {gdp["2025"]:.1f}% (2025) to {gdp["2026"]:.1f}% (2026) and {gdp["2027"]:.1f}% (2027).</li>
<li><b>For a US firm:</b> by covered interest parity (R − R* ≈ {-gap:.2f}%) the RMB trades at a forward premium of roughly {-gap:.1f}%. Under a random-walk forecast, selling RMB forward on receivables earns that premium and buying RMB forward for payables costs it. Hedge on exposure, not on this view: the random walk beats most exchange-rate forecasts.</li></ul></div>
<div class="grid">{"".join(cards)}</div>
<footer><b>Transformations:</b> USD/CNY monthly = average of daily Fed H.10 rates; CPI YoY computed from index levels; policy rates are BIS end-of-period monthly values; no series is rebased. <b>Limitations:</b> LPR is a bank-lending benchmark, not a risk-free rate, so the covered-interest calculation is approximate; IMF figures for 2026+ are projections; the reserves series lags about five months; the real-rate benchmark window (≈16 months) is short; this dashboard does not model capital flows, the PBoC daily fixing or trade policy. Code, refresh instructions and verification: see README.md and VERIFICATION.md.</footer>
</main><div id="tip"></div><script>{JS % json.dumps(ptsall)}</script></body></html>"""
(ROOT/"index.html").write_text(page)
print("wrote index.html", len(page)//1024, "KB")
