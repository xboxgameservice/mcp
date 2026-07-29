# Contributing

This repository holds client configuration, skills, and examples for the Magellan Data
Spotlight MCP server. The server itself is hosted and closed-source; what lives here is the
connective tissue around it.

## What's most useful

**Skills.** If you've built a repeatable workflow on top of these tools — a territory
planning routine, a specific CRM join, a scoring model that works for your segment — that's
the highest-value contribution. Add a directory under `skills/` with a `SKILL.md` following
the shape of the existing ones: frontmatter with `name` and a trigger-rich `description`,
then steps, output shape, and cautions.

**Client configs.** MCP client support moves quickly. If you've got a working config for a
client we haven't covered, send it.

**Examples.** Working code that shows the pipeline in a language or framework we don't have
yet.

## Reporting problems

Open an issue. Useful details:

- Which client and version
- What you asked for
- What the agent did instead
- Whether credits were spent

**Never paste an API key into an issue.** If you think a key has been exposed, rotate it in
the Spotlight dashboard immediately.

For data quality problems (a wrong parent company, a stale PE relationship) an issue works,
but reaching out through https://magellandata.io or email at [support@magellandata.io](mailto:support@magellandata.io) will usually get it corrected faster.

## Pull requests

Fork, branch, open a PR against `main`. Keep skills focused on one job; a skill that tries to
do everything triggers unreliably. Validate JSON before submitting:

    python -c "import json,sys; json.load(open(sys.argv[1]))" server.json
