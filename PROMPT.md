# Prompt given to the AI coding agent

> Edit this file so it matches what you actually typed. This is the instruction set that reproduces the build.

I am a Kellogg MBA student in FINC 470 (International Finance). Build a Country Dashboard for **China**.

**Question the dashboard must answer:** Do China's exchange rate, prices, interest rates and external balance point to RMB depreciation pressure over the next 1-2 years, and what does that imply for a US firm with RMB cash flows?

**Requirements (from the assignment)**
1. Choose 4-8 indicators from reliable primary sources (central banks, statistical agencies, international organizations); no social media. For every chart show units, data frequency, source and latest observation date. State exchange-rate quotation conventions (class convention: CNY per USD) and explain every transformation (growth rates, rebasing). Choose sample periods long enough to interpret recent developments.
2. Automate: fetch data and rebuild the charts on a schedule. Show the date/time of the last successful refresh *separately* from each series' latest observation date. Check at least one observation from every series against its original source, and document a successful refresh (log or screenshot).
3. Deliver the dashboard (HTML), the code, this prompt, and evidence of verification.

**Technical constraints:** Python standard library only; self-contained HTML (no CDN); if one series fails to download, keep its previous values and flag it as stale instead of failing silently; GitHub Actions cron for the schedule.

**Indicators used:** USD/CNY (Fed H.10), BIS real effective exchange rate, China and US CPI inflation, China 1-year LPR vs US policy rate (BIS), IMF real GDP growth, IMF current account/GDP, IMF-IFS reserves.

**Interpretation to include:** relative PPP, real exchange rate vs benchmark, covered interest parity and the forward premium, hedging implications. Report limitations and do not overclaim.
