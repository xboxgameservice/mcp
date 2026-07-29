---
name: ownership-enrichment
description: Enrich a list of companies in place with parent company and PE ownership columns, returned as a file the user can drop back into their CRM or spreadsheet. Use when the user hands over a CSV or spreadsheet of accounts and wants ownership data appended. Triggers on "enrich this list", "add parent company", "which of these are PE-backed", or an uploaded account file.
---

# Ownership Enrichment

Take the user's account list, append ownership columns, hand back a file in the same shape
they gave you.

## Steps

1. **Read the file and find the domain column.** Look for `website`, `domain`, `url`, or
   `company_url`. Report how many rows have a usable domain and how many don't — rows
   without one can't be enriched and shouldn't be silently dropped.

2. **Quote the cost up front.** `parent_companies` and `pe_ownership` are both flat 70
   credits per URL, so the arithmetic is exact before anything runs:

   > 200 valid domains × 70 credits × 2 output types = **28,000 credits**

   Check the balance with `check_credits` and confirm the user wants to spend it. If they
   only need one of the two, say so — it halves the cost.

3. **Run the pipeline.** `submit_batch(domains)` → `process_batch(batch_id, types)` → poll
   `get_run_status` every 10–30 seconds until `completed`. Large batches take minutes.
   Don't poll in a tight loop.

4. **Download and join.** Fetch the presigned CSV (no auth header needed) and join back to
   the original rows on `input_url`. Preserve every original column and every original row,
   including the ones that couldn't be enriched — leave those cells blank rather than
   dropping the row.

5. **Write the output.** Same format the user gave you. If they uploaded `.xlsx`, give back
   `.xlsx`. Name it clearly, e.g. `accounts_enriched.xlsx`.

6. **Summarize.** How many matched, how many are PE-backed, how many are subsidiaries, and
   anything that stands out — a cluster of accounts under one parent is worth flagging
   unprompted.

## Suggested columns to append

| Column | Source |
|---|---|
| `parent_company` | `parent_companies` |
| `parent_company_url` | `parent_companies` |
| `is_pe_backed` | derived from `pe_ownership` |
| `pe_firm` | `pe_ownership` |
| `pe_firm_url` | `pe_ownership` |
| `deal_type` | `pe_ownership` |

## Cautions

- Batches cap at 5,000 URLs. Chunk larger lists and tell the user you're doing it.
- Never overwrite the user's source file. Always write a new one.
- If a download link has expired (HTTP 403 with `Request has expired`), just call
  `download_run` again — re-downloads are free.
