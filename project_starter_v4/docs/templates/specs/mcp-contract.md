# MCP Contract

<!--
  For: AI / LLM Application
  Purpose: Documents every MCP (Model Context Protocol) server this app connects to —
           which servers, what transport, what tools/resources/prompts each exposes,
           and how the app governs tool use at runtime.
  Update when: A server is added or removed, a tool schema changes, transport config changes,
               or tool-use policy is tuned.

  Relationship to other docs:
    llm-contract.md  — model config, system prompt, parameters (link back here for MCP tools)
    rag-contract.md  — if a server wraps a vector store, cross-reference here
-->

## MCP Client Configuration

| Property | Value |
|---|---|
| MCP SDK / client library | [e.g., @anthropic-ai/mcp, mcp (Python), Claude Desktop built-in] |
| Config file location | [e.g., claude_desktop_config.json / mcp_config.json / inline in app code] |
| Default transport | [stdio / SSE / HTTP Streaming] |

---

## Connected Servers

<!--
  One row per MCP server. Add detail blocks below for each server.
-->

| Server name | Transport | Purpose | Status |
|---|---|---|---|
| `[server-name]` | [stdio / SSE / HTTP] | [What this server provides] | [Active / Disabled] |
| `[server-name]` | [stdio / SSE / HTTP] | [What this server provides] | [Active / Disabled] |

---

## Server Detail

<!--
  Repeat this block for each server in the table above.
  For stdio servers: fill in Command and Args; remove URL.
  For SSE / HTTP servers: fill in URL; remove Command and Args.
-->

### `[server-name]`

**Transport:** `stdio`
**Command:** `[e.g., npx / uvx / python -m]`
**Args:** `["[package-or-path]", "[flag]", "[value]"]`

<!-- OR for SSE / HTTP: -->
<!-- **Transport:** `SSE` -->
<!-- **URL:** `[e.g., http://localhost:3000/sse]` -->

**Auth:** `[None / API key header X-API-Key / OAuth / mTLS]`
**Version / package:** `[e.g., @modelcontextprotocol/server-filesystem@0.6.2]`

#### Tools

| Tool name | Description | When LLM should call it |
|---|---|---|
| `[tool_name]` | [What it does] | [Trigger condition — e.g., "user asks about current prices"] |

**Tool schema — `[tool_name]`:**

```json
{
  "name": "[tool_name]",
  "description": "[what this tool does and when to call it]",
  "inputSchema": {
    "type": "object",
    "properties": {
      "[param]": {
        "type": "[string | number | boolean | array | object]",
        "description": "[what this parameter means]"
      }
    },
    "required": ["[param]"]
  }
}
```

**Expected output format:**

```json
{
  "content": [
    { "type": "text", "text": "[example output]" }
  ]
}
```

#### Resources

<!--
  Remove this section if this server exposes no resources.
  Resources are read-only data the LLM can request by URI.
-->

| URI template | MIME type | Description |
|---|---|---|
| `[e.g., file:///data/{filename}]` | `[e.g., text/plain]` | [What this resource contains] |
| `[e.g., resource://[server]/[name]]` | `[MIME type]` | [Description] |

#### Prompt Templates

<!--
  Remove this section if this server exposes no prompt templates.
  Prompt templates are pre-built prompt fragments the server offers.
-->

| Template name | Arguments | Description |
|---|---|---|
| `[template-name]` | `[arg1, arg2]` | [What this template generates] |

---

## Tool Use Policy

<!--
  Governs how the LLM is allowed to use tools during a conversation turn.
  These rules should be reflected in the system prompt (see llm-contract.md).
-->

| Property | Value |
|---|---|
| Max tool calls per turn | [e.g., 5 / unlimited] |
| Parallel tool calls | [Allowed / Disabled] |
| Tool call confirmation | [Silent — execute immediately / Prompt user before executing] |
| Restricted tools | [e.g., none / list any tools the LLM must not call autonomously] |

**System prompt hints for tool use:**

> Add these instructions to the system prompt in `llm-contract.md` so the LLM knows
> when and how to use each tool.

```
[e.g.:
- Use the `search_web` tool whenever the user asks about current events or prices.
- Always call `get_portfolio` before giving any personalised advice.
- Do not call `execute_trade` without explicit user confirmation in the same turn.
]
```

---

## Failure Handling

| Scenario | Behaviour |
|---|---|
| Tool call timeout | [e.g., abort after 10 s, return error text to LLM, ask user to retry] |
| Tool returns error | [e.g., pass error message back to LLM as tool result, let LLM explain to user] |
| Server process crashes (stdio) | [e.g., restart server process, surface reconnection error] |
| Server unreachable (SSE / HTTP) | [e.g., disable affected tools, notify user, continue with remaining servers] |
| Schema mismatch (LLM sends wrong args) | [e.g., server returns validation error → LLM self-corrects on next turn] |
