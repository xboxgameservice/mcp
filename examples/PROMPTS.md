# Agent prompt walkthrough

A progression from free to expensive. Every step up to a download costs nothing, so you can
run the first several against a live key without spending a credit.

Bring your own account list — a spreadsheet with a `website` or `domain` column is all the
agent needs.

---

## 1. Confirm the connection — free

> Check my Magellan Data credit balance.

If you get a number back, you're connected. If the agent goes looking through your
filesystem instead of calling the tool, name it explicitly:

> Use the magellan-data server's check_credits tool.

---

## 2. Read a list and plan the work — free

> Read `accounts.xlsx` and tell me how many rows have a usable company website. Then tell me
> what it would cost to find out which of them are PE-backed.

The agent should report the valid-row count and multiply by 70. It shouldn't run anything
yet. This is the step that tells you whether it's handling cost responsibly.

---

## 3. A small real run — a few hundred credits

> Get PE ownership for these three: moosend.com, constantcontact.com, hoteltonight.com.

<500 credits. Small enough to be a rounding error, real enough to prove the whole pipeline
works: submit, process, poll, price, download.

---

## 4. Enrich the full list — thousands of credits

> Get PE ownership for every company in `accounts.xlsx`, then append the results to the
> original file and save it as a new spreadsheet.

The agent should quote the exact cost and wait. For 200 valid domains that's likely over 10k credits.
This is where you find out whether the join back to your original rows is clean — check that
row count and column order survived.

---

## 5. Follow the graph — priced per record

> Of the companies in that file, take the five PE firms that show up most often and get me
> their full portfolios.

Now the cost isn't knowable in advance, because `pe_portfolios` is priced per record
returned. The agent has to run the batch, read the price off the completed run, and come
back to you before downloading. One sample run of this shape returned 1,093 records —
21,860 credits.

---

## 6. The actual job

> We just closed Moosend. Find every other company owned by the same PE firm, cross-
> reference against `accounts.xlsx`, and give me a ranked list of expansion targets we
> aren't already selling to.

This chains everything: ownership lookup, portfolio expansion, a join against your CRM
export, and a judgment call about ordering. It's what the `account-expansion` skill exists
to make repeatable.

---

## Things to watch for

- **The agent should never download without stating the price.** If it does, that's a bug —
  please open an issue.
- **Polling takes minutes on large batches.** That's expected. The results are being
  computed, not looked up.
- **A 403 on a download link means it expired,** not that something broke. Ask the agent to
  download again — it's free the second time.
