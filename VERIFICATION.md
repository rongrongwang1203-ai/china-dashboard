# Verification report

Generated 2026-11-22 14:23 UTC; data refresh mode: live; last refresh: 2026-11-22T14:19:25+00:00

## 1. Automated checks (every series)

| Series | Status | Obs | Latest obs | Age (days) | Latest value | In plausible range | Fresh enough |
|---|---|---|---|---|---|---|---|
| usdcny_d | stale | 51 | 2026-11-13 | 9 | 6.671 | yes | yes |
| usdcny_m | stale | 58 | 2026-10-01 | 52 | 6.684 | yes | yes |
| reer | ok | 46 | 2026-10 | 25 | 92.92 | yes | yes |
| cpi_cn_yoy | ok | 21 | 2026-09 | 55 | 0.9 | yes | yes |
| cpi_us_yoy | stale | 17 | 2026-09 | 55 | 3.72 | yes | yes |
| pol_cn | ok | 58 | 2026-10 | 25 | 3 | yes | yes |
| pol_us | ok | 58 | 2026-10 | 25 | 3.875 | yes | yes |
| gdp | stale | 14 | 2028 | -767 | 4 | yes | yes |
| ca | stale | 14 | 2028 | -767 | 3.9 | yes | yes |
| reserves | stale | 30 | 2026-06-01 | 174 | 3.482 | yes | yes |

## 2. Internal consistency

| Check | Computed | Reported | Pass |
|---|---|---|---|
| Mean of daily USD/CNY, 2026-09 | 6.7084 | 6.7084 (monthly series) | yes |
| Mean of daily USD/CNY, 2026-10 | 6.6844 | 6.6844 (monthly series) | yes |

## 3. Spot-checks against original sources

| Series | Date | Dashboard | Original source value | Difference | Tolerance | Pass | Source | Note |
|---|---|---|---|---|---|---|---|---|
| usdcny_d | 2026-11-13 | 6.671 | 6.671 | +0.0000 | ±0.0001 | yes | [Federal Reserve Board H.10 release (16 Nov 2026)](https://www.federalreserve.gov/releases/h10/current/) | Dashboard pulls the same H.10 series via FRED. |
| cpi_cn_yoy | 2026-09 | 0.9 | 0.9 | +0.0000 | ±0.05 | yes | [National Bureau of Statistics, CPI September 2026 (14 Oct 2026)](https://www.stats.gov.cn/english/PressRelease/202610/t20261015_1965500.html) | YoY computed from BIS index; NBS reports 0.9%. |
| cpi_us_yoy | 2026-09 | 3.72 | 3.7 | +0.0200 | ±0.1 | yes | [US BLS CPI release, September 2026 (14 Oct 2026)](https://www.bls.gov/news.release/cpi.nr0.htm) | BLS headline is not seasonally adjusted; dashboard uses the SA index, so a rounding gap of <=0.1pp is expected. |
| pol_cn | 2026-10 | 3 | 3.0 | +0.0000 | ±0.0 | yes | [PBoC 1-year LPR announcement, 20 Oct 2026 (unchanged at 3.0%)](https://www.pbc.gov.cn/en/) | Confirmed via press reports of the PBoC fixing; BIS series is the 1-year LPR. |
| pol_us | 2026-10 | 3.875 | 3.875 | +0.0000 | ±0.0 | yes | [Fed funds target range 3.75-4.00% (upper bound 4.00 via FRED DFEDTARU)](https://fred.stlouisfed.org/series/DFEDTARU) | BIS reports the midpoint of the target range. |
| gdp | 2025 | 5 | 4.96 | +0.0400 | ±0.1 | yes | [World Bank WDI NY.GDP.MKTP.KD.ZG (cross-check of IMF)](https://api.worldbank.org/v2/country/CHN/indicator/NY.GDP.MKTP.KD.ZG?format=json) | IMF 5.0 vs World Bank 4.96. |
| ca | 2025 | 3.7 | 3.77 | -0.0700 | ±0.1 | yes | [World Bank WDI BN.CAB.XOKA.GD.ZS (cross-check of IMF)](https://api.worldbank.org/v2/country/CHN/indicator/BN.CAB.XOKA.GD.ZS?format=json) | IMF 3.7 vs World Bank 3.77. |
| reserves | 2026-06-01 | 3.482 | 3.4163 | +0.0661 | ±0.1 | yes | [SAFE, FX reserves end-June 2026 (USD 3.4163 trillion)](https://www.safe.gov.cn/en/2026/0707/2436.html) | DEFINITION GAP: IMF 'total reserves excl. gold' (3.482) is ~0.066tn above SAFE's FX-reserves headline (3.4163), consistent with the IMF series also counting SDRs and the IMF reserve position (inference, not stated by either source). Gap was the same (~0.066-0.067tn) in May and June 2026. |

Series without an independent second source: reer (taken directly from the primary publisher's API; covered by sanity checks only). `usdcny_m` is checked through the daily series above.

**Result: 6 CHECK(S) FAILED**
