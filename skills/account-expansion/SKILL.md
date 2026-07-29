---
name: account-expansion
description: Find warm expansion targets from an existing customer's ownership graph. Use when the user has closed or is close to closing an account and wants to know who else they can sell to through the same parent company or PE firm. Triggers on phrases like "who else can we sell to", "expansion targets", "sister companies", "same PE firm", or "land and expand".
---

# Account Expansion

Turn one closed-won account into a ranked list of warm targets by walking its ownership
graph.

## The logic

A company you already sell to is connected to other companies two ways:

1. **Corporate family** — subsidiaries and sister companies under the same parent. The
   parent often has shared procurement, a shared MSA, and internal referral paths.
2. **PE portfolio** — companies held by the same private equity firm. PE firms actively
   push vendor standardization across their portfolio, and a reference from one portfolio
   company carries real weight with the others.

Both are warmer than cold outbound because there's a structural reason for the
introduction to happen.

## Steps

1. **Establish the anchor.** Confirm which account is the anchor and get its domain. If
   the user gave you a company name, ask for the domain or website rather than guessing.

2. **Check the balance.** Call `check_credits` first. It's free, and it prevents starting a
   pipeline you can't finish.

3. **Resolve ownership.** `submit_batch([anchor_domain])`, then
   `process_batch(batch_id, ["pe_ownership", "parent_companies"])`. Poll
   `get_run_status` until both runs are `completed`. This costs 140 credits total at
   download (70 each, flat) — state that and confirm before downloading.

4. **Branch on what you find:**
   - **PE-backed** → take the firm, `submit_batch([firm_domain])` →
     `process_batch(batch_id, ["pe_portfolios"])`. This is priced per record, so read the
     `price` off the completed run and surface it before downloading.
   - **Has a corporate parent** → take the parent, then
     `process_batch(batch_id, ["corporate_families"])`. Also per record.
   - **Neither** → say so plainly. A standalone independent company has no ownership graph
     to walk, and this play doesn't apply. Don't pad the answer.

5. **Rank the results.** Don't hand back raw rows. Order them by:
   - **Similarity to the anchor** — same industry and rough size band first
   - **`deal_type`** — recent buyouts and add-ons signal active integration and budget
     movement; legacy holdings are colder
   - **Whether they're already in the user's CRM** — if the user gave you an account list,
     split the output into *already covered* and *net new*

6. **Deliver.** A short table: company, domain, relationship to anchor, why now. Then two
   or three sentences on which one to approach first and what the opening line should be.

## Output shape

```
Anchor: Moosend (moosend.com) — acquired by Sitecore, 2021

Warm targets via corporate family (12 found, 4 already in your CRM):

| Company | Domain | Relationship | Why now |
|---|---|---|---|
| ... | ... | Sister company under Sitecore | Same buyer persona, shared procurement |

Start with X. You can reference the Moosend rollout directly — same parent, and their
procurement runs through the same team.
```

## Cautions

- Every output row carries `input_url`, so joining back to the user's original list is
  reliable. Use it rather than fuzzy name matching.
- Overlapping inputs are charged per input. If the user hands you five accounts that share
  a PE firm, tell them — they can submit one firm domain instead of five company domains.
- Never call `download_run` without stating the price first. Per-record output types
  (`pe_portfolios`, `corporate_families`) can return thousands of rows, and the cost scales
  with them.
