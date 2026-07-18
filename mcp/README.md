# @toorpia/mcp — toorPIA MCP Server (Embedding Analysis)

An [MCP](https://modelcontextprotocol.io/) server that lets AI clients (Claude Desktop, Claude Code, Cursor, …) analyze **embedding vectors** with the [toorPIA](https://toorpia.com/) API.

toorPIA is a dimensionality-reduction and anomaly-detection service built on an O(n) Laplacian-eigenmaps implementation. Unlike t-SNE/UMAP, results are **deterministic** (same input → same map) and new data can be **added to an existing map without recomputation**, so coordinates stay comparable over time. This makes it well suited for monitoring embedding drift, detecting anomalous batches against a learned baseline, and reproducible visual exploration of embedding spaces.

The server runs locally on your machine (stdio transport), reads embedding CSV files from your local disk, and sends them to the toorPIA API using your personal API key. Uploads are gzip-compressed automatically. Full 2-D coordinates are never returned into the AI conversation — results come back as compact statistical summaries plus a `shareUrl` you can open in a browser for interactive inspection.

## Tools

| Tool | What it does |
|---|---|
| `preview_csv` | Inspect a local embedding CSV **without uploading**: rows, dimensions, header/ID-column detection, L2-norm statistics, sample rows. |
| `create_basemap` | Upload baseline embeddings and build the 2-D reference map. Returns `mapNo`, `shareUrl`, and a distribution summary. |
| `add_plot` | Project new embeddings onto an existing map and run anomaly detection. Returns abnormality status/score, a composite diagnostic (normal / warning / danger), and `shareUrl`. |
| `list_maps` | List the maps that belong to your API key (newest first). |

### Input data format

- `.csv` or gzip-compressed `.csv.gz`
- Rows = samples, columns = embedding dimensions
- An optional header row and leading non-numeric ID/label columns are auto-detected by the server
- `add_plot` files must have exactly the same embedding dimensionality as the basemap (preprocessing is inherited from the basemap automatically)

## Requirements

- Node.js **18 or newer** (`node --version`)
- A toorPIA API key (issued individually — contact your toorPIA representative)

## Setup

### Claude Desktop

Edit the config file (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`, Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "toorpia": {
      "command": "npx",
      "args": ["-y", "@toorpia/mcp"],
      "env": {
        "TOORPIA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop afterwards. The toorPIA tools appear in the tools menu.

### Claude Code

```bash
claude mcp add toorpia -e TOORPIA_API_KEY=your-api-key-here -- npx -y @toorpia/mcp
```

Or add to `.mcp.json` in your project (or `~/.claude.json` for all projects):

```json
{
  "mcpServers": {
    "toorpia": {
      "command": "npx",
      "args": ["-y", "@toorpia/mcp"],
      "env": {
        "TOORPIA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` globally):

```json
{
  "mcpServers": {
    "toorpia": {
      "command": "npx",
      "args": ["-y", "@toorpia/mcp"],
      "env": {
        "TOORPIA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TOORPIA_API_KEY` | yes | — | Your personal toorPIA API key. |
| `TOORPIA_API_URL` | no | `https://api.toorpia.com` | toorPIA API endpoint. Set this for on-premise installations. |

## Example session

> **User:** I have sentence embeddings of last month's support tickets in `/data/tickets_baseline.csv`. Map them, then check whether this week's tickets in `/data/tickets_w29.csv` look unusual.

The AI client will typically:

1. `preview_csv` both files (confirm same dimensionality, decide preprocessing)
2. `create_basemap` with the baseline file → returns `mapNo` + `shareUrl`
3. `add_plot` with the new file → returns abnormality verdict + `shareUrl`
4. Explain the verdict and hand you the `shareUrl` links for visual inspection

## Verifying the server with MCP Inspector

To check connectivity independently of any AI client:

```bash
cd mcp            # this directory (when working from the repository)
npm install && npm run build

npx @modelcontextprotocol/inspector \
  -e TOORPIA_API_KEY=your-api-key-here \
  node dist/index.js
```

Then in the Inspector UI that opens in your browser:

1. Press **Connect** — the server banner should appear in the console (`[toorpia-mcp] server started`)
2. Open **Tools → List Tools** — the four tools should be listed
3. Call `preview_csv` with `{"path": "<absolute path>/testdata/embedding_sample.csv"}` — returns row/dimension statistics without touching the API
4. Call `list_maps` with `{}` — verifies authentication against the API (`AUTH_FAILED` here means the API key is wrong)

For the published package, replace `node dist/index.js` with `npx -y @toorpia/mcp`.

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| Error `AUTH_MISSING` | `TOORPIA_API_KEY` is not set in the MCP server config. Add it to the `env` block and restart the client. |
| Error `AUTH_FAILED` | The API key is invalid or expired. Verify the key (no surrounding quotes/whitespace) or request a new one. |
| Error `NETWORK_ERROR` | The server cannot reach `TOORPIA_API_URL`. Check the URL, your network/VPN, and any proxy settings. |
| Server does not appear in the client | Run `npx -y @toorpia/mcp` once in a terminal to see startup errors. Common causes: Node < 18, `npx` not on the PATH the client uses (on macOS GUI apps, install Node via the official installer or set an absolute path to `npx`). |
| `spawn npx ENOENT` (Windows) | Use `"command": "npx.cmd"` or an absolute path to `npx`. |
| `add_plot` fails with a dimension-mismatch message | The new CSV has a different number of embedding dimensions than the basemap. Run `preview_csv` on both files and compare `embeddingDimensions`. |
| `add_plot` fails with a process-method mismatch | The target map was not created from embeddings (e.g. a CSV/waveform map). Use `list_maps` and pick a map created by `create_basemap`. |
| `create_basemap` on a large file seems stuck | Processing is synchronous and can take minutes for large datasets. The server waits up to 30 minutes. Keep the file as `.csv.gz` to shorten the upload. |
| HTTP 415 on upload | Older API servers reject gzip-compressed uploads; the server automatically retries uncompressed. If it still fails, the file itself is not valid CSV. |
| Tool responses look stale after an update | `npx` may cache an old version. Run `npx -y @toorpia/mcp@latest`, or clear the cache with `npm cache clean --force`. |

## Development

```bash
cd mcp
npm install
npm run build     # compile to dist/
npm run dev       # run from TypeScript sources (tsx)
```

Source layout:

```
src/
├─ index.ts     # bin entry point
├─ server.ts    # MCP server + tool definitions
├─ api.ts       # toorPIA API client (auth, gzip upload, retries)
├─ preview.ts   # local embedding-CSV inspection
├─ summary.ts   # 2-D distribution summary statistics
└─ errors.ts    # unified {ok, code, reason} error payloads
```

`testdata/embedding_sample.csv` (60 rows × 16 dims, 2 clusters) and `embedding_addplot_sample.csv` are small deterministic fixtures for manual testing.

## Publishing (maintainers)

The package is published as `@toorpia/mcp`. One-time setup: create the free npm organization `toorpia` (npmjs.com → Add Organization) with the publishing account as owner. Then:

```bash
cd mcp
npm publish --access public
```

`prepublishOnly` builds `dist/` automatically; only `dist/` and `README.md` are included in the package.
