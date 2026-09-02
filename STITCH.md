# Stitch MCP (Google)

Apex F1 Suite can use [Google Stitch](https://stitch.withgoogle.com/) so an agent can pull design screens into this repo. Official setup: [Stitch MCP setup](https://stitch.withgoogle.com/docs/mcp/setup).

This workspace already lists a **Stitch** MCP server in [`.mcp.json`](./.mcp.json) and [`.cursor/mcp.json`](./.cursor/mcp.json) as:

```json
"stitch": {
  "command": "npx",
  "args": ["-y", "@_davideast/stitch-mcp", "proxy"]
}
```

That is the documented proxy for Cursor ([`@_davideast/stitch-mcp`](https://github.com/davideast/stitch-mcp)). It talks to Google’s MCP endpoint (`https://stitch.googleapis.com/mcp`) without putting an API key in git.

## One-time auth (your machine)

```bash
npx @_davideast/stitch-mcp init
```

The wizard installs/configures gcloud if needed, OAuth, and project selection. Alternative: set `STITCH_API_KEY` in the environment (never commit it).

If gcloud is already logged in:

```bash
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
gcloud beta services mcp enable stitch.googleapis.com --project=<PROJECT_ID>
```

Then set `STITCH_USE_SYSTEM_GCLOUD=1` on the MCP server env in Cursor.

Reload Cursor MCP after auth. Ask the agent to list Stitch projects or fetch a screen.

## What this app does not do

Stitch does **not** run in production (Vercel/Railway). It is an **editor** design source. The shipped UI is Next.js + Tailwind + shadcn. Screen inventory: [FEATURES.md](./FEATURES.md).
