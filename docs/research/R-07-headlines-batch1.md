# R-07 batch 1 — curated news headlines

R-07 batch 1 — curated news headlines, window 2026-08-24..2026-09-23, source Gemini research; URLs verified by hand on 2026-10-21. Headlines/links only; no numbers from the research narrative are used anywhere.

## Verified rows

```csv
symbol,published_date,source,headline,url
OGDC,2026-09-04,DAWN,OGDCL announces record Rs242.4bn profit for fiscal year 2025-26,https://www.dawn.com/news/2027502
OGDC,2026-09-05,BR,"OGDCL posts highest-ever annual profit, dividend",https://www.brecorder.com/news/40438005
OGDC|MARI,2026-09-09,BR,"OGDCL, MARI-backed Lundali-1 well starts gas production in Sindh",https://www.brecorder.com/news/40438614
OGDC,2026-09-14,BR,OGDC: Tax reversal powers record profit,https://www.brecorder.com/news/40439335
```

## Dropped / held

- a) OGDC 2026-09-10 BR "OGDCL starts gas production from Lundali-1 well in Sindh" (https://www.brecorder.com/news/40438764/...) — dropped, same event as 2026-09-09.
- b) ENGROH 2026-09-02 BR "Engro to sell entire EPCL stake to Lotte for Rs19.7bn" (epaper.brecorder.com URL) — was held (URL unverified); now covered, see "Substitute" below.
- c) Gemini returned no qualifying headlines for PPL, HUBC, PSO in this window.

## Import notes

Imported as `data/manual/news_R-07_batch1.csv`. Rows 2026-09-05 and 2026-09-09 already exist in the DB from R-06 (same URL, same symbols), so they are left out of the import file; the other 2 are new.

## Substitute (R07-SOURCES)

ENGROH 2026-09-02 TRIBUNE "Engro to sell 56% stake in EPCL for Rs19.7b" (https://tribune.com.pk/story/2626987/engro-to-sell-56-stake-in-epcl-for-rs197b) — imported as the Tribune substitute; no brecorder.com web article found. **Not imported**: news #95 (R-06, BR 2026-09-01 "Engro to sell entire EPCL stake to Lotte for Rs197bn") already covers the same event, and headlines count one per event per ticker (D-65).
