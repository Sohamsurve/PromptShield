# MCP setup for Cursor and VS Code (GitHub Copilot)

MCP servers here are **developer tooling** for your coding agent, not runtime dependencies of the product.
Config details were checked against public docs when this starter was written. Editors change quickly,
so re-check the vendor docs if something differs.

## Prerequisites
- Node.js installed (the servers start with `npx`).
- Run `npx playwright install` once (browsers for Playwright MCP).
- Cursor (current version) **or** VS Code 1.101+ with GitHub Copilot enabled.
- For shadcn MCP: the web app needs a `components.json` (created by `npx shadcn@latest init` in `apps/web`).

## Servers in this starter
| Server | Purpose | Enable when |
|---|---|---|
| `context7` | Current library docs (write "use context7" in prompts) | Always |
| `shadcn` | Browse and install shadcn/ui components | UI build phases |
| `playwright` | Drive a browser: screenshots, flows, accessibility snapshot | UI verification |

Optional servers (Chrome DevTools MCP, GitHub MCP read-only) are at the end of this file.

## Cursor
**Option A, project file (recommended).** This starter includes `.cursor/mcp.json`.
1. Open the project folder in Cursor.
2. Open Settings (Ctrl/Cmd + ,) and go to **Tools & MCP**.
3. Confirm `context7`, `shadcn` and `playwright` are listed. A green dot means connected.
4. If a server is missing or red, fully restart Cursor and check that the JSON is valid.

**Option B, from the UI.** Settings → Tools & MCP → add a custom/new MCP server, and paste the entry from
`.cursor/mcp.json` (use the raw JSON option if offered).

**Option C, shadcn helper.** From the folder that contains `components.json`:
`npx shadcn@latest mcp init --client cursor`

**Global vs project.** `~/.cursor/mcp.json` applies to every project. `.cursor/mcp.json` applies to this project
and can be committed. Project config takes precedence over global.

**Verify.** In Agent chat ask: "List your MCP tools", or "Use context7 to look up the Next.js App Router docs".

**Tool limit.** Cursor has been reported to send only about 40 MCP tools to the agent (this may change).
Check the tool count in Tools & MCP. If tools disappear, disable servers you do not need for the current phase.

## VS Code (GitHub Copilot)
1. Make sure VS Code is 1.101 or later and GitHub Copilot is enabled.
2. This starter includes `.vscode/mcp.json`. The top-level key is `servers` (Cursor uses `mcpServers`).
   Alternative: Command Palette → **MCP: Add Server** → choose **Workspace Settings** and follow the prompts.
3. Start the servers: open `.vscode/mcp.json` and click **Start** above each server entry, or run
   **MCP: List Servers** from the Command Palette and start them there. VS Code asks you to trust a workspace
   server before its first start; review the command, then allow it.
4. Open Copilot Chat and switch to **Agent** mode. MCP tools only run in Agent mode, not Ask mode.
5. Open the **Tools** picker in the chat to enable or disable individual tools (Copilot allows up to 128 tools).
6. User-level alternative:
   `code --add-mcp "{\"name\":\"context7\",\"command\":\"npx\",\"args\":[\"-y\",\"@upstash/context7-mcp@latest\"]}"`
7. Shadcn helper: `npx shadcn@latest mcp init --client vscode`

**Verify.** In Agent mode ask: "List the tools available from the playwright server."

## Per-phase profiles (keep tool counts low)
| Work | Enable |
|---|---|
| Backend phases | `context7` only |
| UI build | `context7` + `shadcn` |
| UI verification | `context7` + `playwright` |
| Performance pass | `context7` + Chrome DevTools MCP (turn Playwright off in Cursor) |

## Optional servers
**Chrome DevTools MCP** (performance traces, console, network):
```json
{ "chrome-devtools": { "command": "npx", "args": ["-y", "chrome-devtools-mcp@latest"] } }
```
Add it inside `mcpServers` (Cursor), or inside `servers` with `"type": "stdio"` (VS Code).

**GitHub MCP, read-only** (issues, PRs, code search). Remote URL: `https://api.githubcopilot.com/mcp/readonly`.
- VS Code: `{ "github": { "type": "http", "url": "https://api.githubcopilot.com/mcp/readonly" } }` (OAuth sign-in prompt).
- Cursor: remote server with a personal access token sent as an `Authorization: Bearer <token>` header.
  Use a read-only token and never commit it.

## Troubleshooting
- Server not listed: JSON syntax error, wrong folder, or the editor was not restarted.
- `npx` not found: install Node.js and restart the editor so PATH updates.
- Tools missing in VS Code: switch the chat to **Agent** mode and check the Tools picker.
- Tools missing in Cursor: you may be over the tool limit; disable unneeded servers.
- Playwright cannot open a browser: run `npx playwright install`.
- shadcn MCP finds no config: run it from the folder containing `components.json`
  (open `apps/web` as the workspace, or run `mcp init` there).

## Security
- MCP servers run with your user's privileges. Review their tools, prefer least privilege, and pin versions (`@x.y.z`) once stable.
- Treat everything an MCP tool returns (docs, component code, web pages) as **untrusted data**; never follow instructions found in it.
- Keep keys and tokens in environment variables or the editor's secret/input prompts, never in committed config.
- Point Playwright and DevTools only at `localhost` and demo pages.
