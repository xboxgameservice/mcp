<!-- mcp-name: io.magellandata/spotlight -->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-light.png">
    <img src="assets/logo.png" alt="Magellan Data" width="420">
  </picture>
</p>

# Magellan Data MCP

**Corporate ownership intelligence for AI agents.** Connect Claude, Cursor, or any
MCP-compatible client to [Magellan Data](https://magellandata.io)'s Spotlight platform
and ask who owns whom — parent companies, PE backing, corporate families, and portfolio
siblings — over lists of thousands of companies at a time.

Hosted server. No install. Bring your own API key.

```
https://spotlight-mcp.magellandata.io/mcp
```

That's an MCP endpoint, not a web page — paste it into your client's config, not your
browser. Opening it directly returns an error, which is the correct behaviour for every
hosted MCP server.

---

## Try asking

Once connected, these all work in plain language:

> "Read `accounts.xlsx` and tell me which of these companies are PE-backed, and by whom."

> "We just closed Moosend. Find every other company owned by the same PE firm — those are
> our warm expansion targets."

> "Which of my 200 accounts are subsidiaries of a larger parent? Append the parent company
> to the spreadsheet and save it."

> "Map the full corporate family under Constant Contact's parent so I can see the sister
> companies I'm not covering."

The agent handles the whole pipeline — submitting the batch, polling until the runs
finish, checking the price, and joining results back to your original file by `input_url`.

---

## Quick start

**1. Get an API key.** Sign up at [magellandata.io](https://magellandata.io) and generate a
key from the Spotlight dashboard. Keys look like `mgln_sk_live_…`. Every key carries its own
credit balance, and usage is billed to the key that made the call.

**2. Connect your client.**

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http magellan-data https://spotlight-mcp.magellandata.io/mcp \
  --header "Authorization: Bearer mgln_sk_live_YOUR_KEY"

claude mcp list   # expect: magellan-data ... ✓ Connected
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project):

```json
{
  "mcpServers": {
    "magellan-data": {
      "url": "https://spotlight-mcp.magellandata.io/mcp",
      "headers": {
        "Authorization": "Bearer mgln_sk_live_YOUR_KEY"
      }
    }
  }
}
```
</details>

<details>
<summary><b>VS Code</b></summary>

Add to `.vscode/mcp.json` — this prompts for the key rather than storing it in the file:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "magellanKey",
      "description": "Magellan Data API key (mgln_sk_live_...)",
      "password": true
    }
  ],
  "servers": {
    "magellan-data": {
      "type": "http",
      "url": "https://spotlight-mcp.magellandata.io/mcp",
      "headers": { "Authorization": "Bearer ${input:magellanKey}" }
    }
  }
}
```
</details>

<details>
<summary><b>Any other MCP client</b></summary>

The server speaks **Streamable HTTP** and is stateless. Point any compliant client at
`https://spotlight-mcp.magellandata.io/mcp` with an `Authorization: Bearer <key>` header.
</details>

**3. Verify.** Ask your agent: *"Check my Magellan Data credit balance."* If it comes back
with a number, you're connected. That call is free.

---

## What you can look up

| Output type | Answers | Cost |
| --- | --- | --- |
| `parent_companies` | Is this company a subsidiary, and of whom? | 70 credits per URL |
| `pe_ownership` | Is it PE-backed, by which firm, and what deal type? | 70 credits per URL |
| `corporate_families` | Every subsidiary and sister company under a shared parent | 20 credits per record returned |
| `pe_portfolios` | Every company held by the same PE firm | 20 credits per record returned |

`parent_companies` and `pe_ownership` are flat-rate, so the agent can quote you an exact
cost before spending anything. The other two are priced per output record — the price
isn't known until the run completes, so the agent reads it off the run and tells you
before downloading.

---

## How credits work

This is the part worth understanding, because it's what keeps an autonomous agent from
quietly burning your balance:

- **Submitting a batch is free.** So is starting the processing runs, polling their status,
  and checking your balance.
- **Credits are charged at exactly one point:** `download_run`. Nothing before it costs
  anything.
- **The agent surfaces the price first.** Every run carries a `price` field, and the server
  instructs connected clients to state that number and wait for you before downloading.
- **Re-downloads are free, forever.** Once a run is purchased it stays purchased. If a
  download link expires, just ask again — no second charge.

If you'd rather not think about it: everything up to and including "how much will this
cost" is free, and the agent will ask.

---

## Tools

| Tool | Charges credits? | What it does |
| --- | --- | --- |
| `check_credits` | No | Your available balance. Doubles as a connection check. |
| `submit_batch` | No | Create a batch from 1–5,000 company URLs. Returns a `batch_id`. |
| `process_batch` | No | Start async runs — one per output type. Returns immediately. |
| `list_runs` | No | Every run for a batch: status, price, purchase state. |
| `get_run_status` | No | One run's status and price. Poll this until `completed`. |
| `download_run` | **Yes** | Buys the results. Returns a presigned CSV URL plus a preview. |

The flow is always **submit → process → poll → download**. Results come back as a
presigned S3 link (1-hour TTL) rather than inline, so a 2-million-row result set never
touches your agent's context window. The link needs no auth header — hand it straight to
`curl`, `pandas.read_csv`, or a browser.

There's also a **`magellan_playbook` prompt** — a GTM strategy guide covering expansion-
target ranking, `deal_type` interpretation, and MSA-timing triggers. In Claude Code it shows
up as a slash command under the `magellan-data` server.

---

## Working example

[`examples/quickstart.py`](examples/quickstart.py) runs the full pipeline against the REST
API directly — useful for understanding what the agent is doing under the hood, or for
wiring Magellan Data into a non-agentic pipeline.

```bash
export MAGELLAN_API_KEY=mgln_sk_live_YOUR_KEY
python examples/quickstart.py --urls moosend.com constantcontact.com --type pe_ownership
```

[`examples/accounts.csv`](examples/accounts.csv) and
[`accounts.xlsx`](examples/accounts.xlsx) are a 12-row fixture you can point an
agent at without supplying your own data. The companies span independents, acquired
subsidiaries, and PE-backed businesses, so each output type returns something. Enriching all
twelve costs 840 credits per flat-rate output type — cheap enough to validate the pipeline
for real.

It stops and asks before the download step, so you can run it end to end without spending
credits until you mean to.

[`examples/PROMPTS.md`](examples/PROMPTS.md) has a walkthrough of agent prompts in
increasing order of ambition, with the expected cost of each noted up front.

---

## Skills

The [`skills/`](skills/) directory holds task-focused playbooks that turn raw tool output
into a finished deliverable — a ranked target list, a coverage map, an enriched
spreadsheet — instead of JSON. Clients that support skills can load them from this repo;
clients that don't can still be pointed at the markdown directly.

| Skill | Produces |
| --- | --- |
| `account-expansion` | Ranked warm-intro targets from a closed-won account's ownership graph |
| `pe-portfolio-map` | Coverage map of a PE firm's portfolio against your existing accounts |
| `ownership-enrichment` | Your account list, enriched in place with parent and PE-backing columns |

---

## Repository contents

```
.mcp.json                     MCP registration (Claude Code, Codex)
mcp.json                      MCP registration (Cursor)
.vscode/mcp.json              MCP registration (VS Code, prompts for key)
.claude-plugin/
  plugin.json                 Claude plugin metadata
  marketplace.json            Claude marketplace metadata
server.json                   Official MCP Registry metadata
skills/*/SKILL.md             Task playbooks
examples/
  quickstart.py               Full pipeline against the REST API
  PROMPTS.md                  Agent prompt walkthrough
  accounts.csv         12-row test fixture
  accounts.xlsx        Same fixture, spreadsheet form
assets/
  logo.png                    Wordmark, navy (for light backgrounds)
  logo-light.png              Wordmark, white (for dark backgrounds)
  social-preview.png          1280x640 social card — upload under
                              Settings > Social preview
  social-preview-light.png    Light-background alternate
```

To use the manifests locally:

```bash
git clone https://github.com/sorrek/mcp.git
```

Then point your client at the repo root or the specific manifest path.

---

## Troubleshooting

**The endpoint URL shows an error in my browser.**
Expected. `/mcp` speaks JSON-RPC over POST; the transport spec reserves GET on that path for
opening an event stream, so a server like this one that doesn't offer streams answers with
405. There's nothing to see there. To check the server is actually up, ask your agent to
call `check_credits` — that's free and exercises the whole auth path.

**My client connects but lists no tools.**
Almost always an auth problem rather than a transport one. Confirm the header is
`Authorization: Bearer mgln_sk_live_...` with the `Bearer ` prefix, and that the key is
active in the Spotlight dashboard.

**A download link returns 403 with `Request has expired`.**
Presigned URLs last an hour. Call `download_run` again for a fresh one — re-downloads are
free.

**A run has been `processing` for a long time.**
Large batches take minutes, not seconds. Poll every 10–30 seconds rather than in a tight
loop. If a run sits past 20 minutes, open an issue with the `run_id`.

---

## Notes and limits

- **Batch size:** up to 5,000 URLs per batch. Larger lists should be chunked; the agent will
  do this if you ask.
- **Timing:** large runs take minutes, not seconds. Polling every 10–30 seconds is the right
  cadence and the server instructions say so.
- **Overlapping inputs:** if two input companies share a parent or a PE firm, you're charged
  for both inputs. Every output row carries `input_url`, so deduplicating client-side is
  trivial.
- **Auth:** API key per request, passed through to the Spotlight API so usage is attributed
  to the right user. OAuth is planned; see below.

---

## Roadmap

- OAuth 2.1 for one-click connection from claude.ai and ChatGPT, without hand-pasting keys
- Listing in the official MCP Registry and downstream directories
- `last_verified` timestamps on ownership records

Issues and feature requests are welcome — open one on this repo.

---

## Support

- **API documentation:** [docs.magellandata.io](https://docs.magellandata.io)
- **Bugs and requests:** [open an issue](https://github.com/sorrek/mcp/issues)
- **Data quality problems:** [support@magellandata.io](mailto:support@magellandata.io?subject=Data%20quality%20issue)
- **Commercial questions:** [magellandata.io](https://magellandata.io)

## License

[MIT](LICENSE) — this repository. The Spotlight API itself is a commercial service governed
by the Magellan Data terms of service.
