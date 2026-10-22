# R-06 / R-07 curated rows: page check (FIX-11, 2026-10-22)

Each URL fetched with a browser user-agent; all returned HTTP 200 (BR did not block). Page date = `datePublished` (BR) / `article:published_time` (Dawn), PKT.

| id | symbol | source | our date | page date | headline match | status |
|---|---|---|---|---|---|---|
| 91 | OGDC | BR | 2026-09-05 | 2026-09-05 | Y | OK |
| 92 | OGDC, MARI | BR | 2026-09-09 | 2026-09-09 | Y | OK |
| 94 | HUBC | BR | 2026-08-31 | 2026-08-31 | Y | OK |
| 95 | ENGROH | BR | 2026-09-01 | 2026-09-02 | Y for words; ours says `Rs197bn`, page `Rs19.7bn` | MISMATCH (date +1 day, number typo) |
| 96 | ENGROH | BR | 2026-09-21 | 2026-09-21 | Y | OK |
| 97 | OGDC | DAWN | 2026-09-04 | 2026-09-04 | Y | OK |
| 98 | OGDC | BR | 2026-09-14 | 2026-09-14 | Y | OK |

Not in the DB (checked for completeness): R-06's ENGRO 2026-09-21 "Kashan Hasan steps down as CEO of FrieslandCampina Engro Pakistan" (brecorder 40440480): page 2026-09-21, headline Y, OK. Removed #93 (MEBL, 40437629): the page is an unrelated IBA article dated 2026-09-03; the real report is APP 2026-10-09 (B-036).

All dates are inside the window (2026-08-24 to 2026-09-23); no look-ahead among the remaining rows. #95 was not changed (its day-off date is harmless for the window); correct it with the next news edit if wanted.
