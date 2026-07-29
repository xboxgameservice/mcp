---
name: pe-portfolio-map
description: Map a private equity firm's full portfolio and score it against the user's existing account coverage. Use when the user names a PE firm and wants to see everything it holds, or wants to find whitespace in a portfolio they're already partly selling into. Triggers on "portfolio", "what does [firm] own", "coverage gap", "whitespace", or "territory map".
---

# PE Portfolio Map

Produce a coverage map of a private equity firm's holdings: what they own, what you already
sell to, and where the whitespace is.

## Steps

1. **Get the firm's domain.** Portfolio lookups key off the firm's website, not its name.
   If the user says "Vista" or "Thoma Bravo," ask for or confirm the domain.

2. **Check credits.** Free, and portfolio runs can be large.

3. **Pull the portfolio.** `submit_batch([firm_domain])` →
   `process_batch(batch_id, ["pe_portfolios"])` → poll `get_run_status`.

4. **Quote the price before downloading.** `pe_portfolios` is 20 credits per record
   returned, so a large firm can be expensive. The exact number appears on the run once it
   completes. State it and wait. A firm with 400 holdings is 8,000 credits — the user
   should decide, not you.

5. **Overlay the user's accounts.** If they've provided a CRM export or account list, join
   on domain and split into three buckets:
   - **Covered** — already a customer
   - **In flight** — open opportunity
   - **Whitespace** — no relationship yet

6. **Score the whitespace.** Rank by fit against the covered accounts: same industry, same
   size band, similar tech posture. A portfolio company that looks like your best existing
   customer is a better target than one that doesn't, regardless of size.

## Output shape

A summary line (portfolio size, your coverage percentage), then a whitespace table ordered
by fit, then a short note on the two or three strongest plays and what reference story to
lead with.

## Cautions

- Portfolio data reflects current holdings. A company that was exited may still appear
  associated with the firm in some records — check `deal_type` before asserting a live
  relationship.
- If the user asks for several firms at once, submit all the firm domains in a single batch
  rather than one batch per firm. Same cost, far fewer round trips.
