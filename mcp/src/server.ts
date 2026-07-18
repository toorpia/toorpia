import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { ToorpiaApi } from "./api.js";
import { previewEmbeddingCsv } from "./preview.js";
import { summarizeXy } from "./summary.js";
import { ToolError, toErrorPayload } from "./errors.js";

const SERVER_VERSION = "0.1.0";

const INSTRUCTIONS = `toorPIA is a dimensionality-reduction and anomaly-detection service built on an O(n) Laplacian-eigenmaps implementation. Unlike t-SNE/UMAP, results are deterministic and stable across runs, and new data points can be added to an existing map without recomputation, preserving coordinate consistency. This server is specialized for EMBEDDING vectors — LLM sentence/document embeddings, image features, audio embeddings, or any fixed-dimensional numeric vectors — stored as CSV files (rows = samples, columns = dimensions; .csv or .csv.gz).

Best suited for: building a 2-D reference map from baseline embeddings, detecting anomalies/drift in new embedding batches against that baseline, and reproducible visual exploration of embedding spaces.

Typical workflow:
1. preview_csv — inspect a local embedding CSV before uploading (rows, dimensions, ID columns, norm statistics)
2. create_basemap — upload baseline embeddings and build the reference map
3. add_plot — project new embeddings onto an existing map and get an anomaly verdict
4. list_maps — find previously created maps to reuse

Raw 2-D coordinates are summarized, never returned in full; direct the user to the returned shareUrl to explore the map interactively in a browser.`;

interface JsonResult {
  [key: string]: unknown;
}

function jsonContent(payload: JsonResult, isError = false) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(payload) }],
    ...(isError ? { isError: true } : {}),
  };
}

function logTool(name: string, result: "OK" | string, startTime: number): void {
  const status = result === "OK" ? "OK" : `ERROR:${result}`;
  console.error(`[toorpia-mcp] ${name}: ${status} (${Date.now() - startTime}ms)`);
}

async function runTool(name: string, fn: () => Promise<JsonResult>) {
  const start = Date.now();
  try {
    const result = await fn();
    logTool(name, "OK", start);
    return jsonContent(result);
  } catch (error) {
    const payload = toErrorPayload(error);
    logTool(name, payload.code, start);
    return jsonContent(payload, true);
  }
}

const filesSchema = z
  .array(z.string())
  .min(1)
  .describe(
    "Path(s) of embedding CSV files (.csv or .csv.gz). Rows = samples, columns = embedding dimensions; an optional header row and leading ID/label columns are auto-detected by the server. Multiple files are concatenated. Use absolute paths.",
  );

const identnaShape = {
  identna_resolution: z.number().int().optional()
    .describe("Advanced: mesh resolution for normal-area identification (server default 100). Usually leave unset."),
  identna_effective_radius: z.union([z.number(), z.literal("auto")]).optional()
    .describe('Advanced: effective radius for normal-area identification (server default 0.1), or "auto" for data-driven bandwidth. Usually leave unset.'),
  identna_er_method: z.enum(["silverman", "knn"]).optional()
    .describe('Advanced: bandwidth method used when identna_effective_radius="auto".'),
  identna_knn_k: z.number().int().optional()
    .describe("Advanced: k for the knn bandwidth method (0 = auto)."),
};

export async function startServer(): Promise<void> {
  const apiUrl = (process.env.TOORPIA_API_URL ?? "https://api.toorpia.com").replace(/\/+$/, "");
  const api = new ToorpiaApi(apiUrl, process.env.TOORPIA_API_KEY);

  const server = new McpServer(
    { name: "toorpia-mcp", version: SERVER_VERSION },
    { instructions: INSTRUCTIONS },
  );

  server.registerTool(
    "preview_csv",
    {
      title: "Preview embedding CSV",
      description:
        "Inspect a local embedding CSV file (.csv or .csv.gz) WITHOUT uploading it: row count, embedding dimensionality, detected header and ID/label columns, L2-norm statistics, and a few truncated sample rows. Use this before create_basemap to confirm the file really is an embedding matrix and to decide whether l2_normalization or id_columns need to be overridden, or before add_plot to check that dimensions match the basemap.",
      inputSchema: {
        path: z.string().describe("Path to the embedding CSV file (.csv or .csv.gz). Use an absolute path."),
        sample_rows: z.number().int().min(1).max(20).optional()
          .describe("Number of sample rows to return (default 5)."),
      },
    },
    async ({ path, sample_rows }) =>
      runTool("preview_csv", async () => {
        return (await previewEmbeddingCsv(path, sample_rows ?? 5)) as unknown as JsonResult;
      }),
  );

  server.registerTool(
    "create_basemap",
    {
      title: "Create embedding basemap",
      description:
        "Upload baseline embedding CSV file(s) to toorPIA and build a 2-D basemap — the learned reference (\"normal\") distribution for later anomaly detection with add_plot. Results are deterministic (same input, same map) thanks to the O(n) Laplacian-eigenmaps engine, and the map's coordinate system stays fixed when new data is added later. Use this when the user wants to visualize an embedding dataset, establish a baseline for drift/anomaly monitoring, or compare batches of embeddings. Returns mapNo, a browser shareUrl for interactive inspection, and a statistical summary of the resulting 2-D distribution (never the full coordinates). Processing is synchronous and may take a while for large datasets.",
      inputSchema: {
        files: filesSchema,
        label: z.string().optional().describe("Human-readable map name, shown in list_maps. Strongly recommended."),
        tag: z.string().optional().describe("Short classification tag for grouping maps."),
        description: z.string().optional().describe("Longer description of the dataset/purpose."),
        l2_normalization: z.boolean().optional()
          .describe("Server default: true (each vector scaled to unit length; distances reflect direction only). Set false when vector magnitude carries information. preview_csv's norm statistics help decide. The choice is stored on the map and inherited by add_plot."),
        id_columns: z.number().int().min(0).optional()
          .describe("Number of leading ID/label columns in the CSV. Usually auto-detected from non-numeric columns; set explicitly only when the ID columns look numeric."),
        ...identnaShape,
      },
    },
    async (args) =>
      runTool("create_basemap", async () => {
        const result = await api.basemapEmbedding({
          files: args.files,
          label: args.label,
          tag: args.tag,
          description: args.description,
          l2Normalization: args.l2_normalization,
          idColumns: args.id_columns,
          identna: {
            resolution: args.identna_resolution,
            effectiveRadius: args.identna_effective_radius,
            erMethod: args.identna_er_method,
            knnK: args.identna_knn_k,
          },
        });
        return {
          ok: true,
          mapNo: result.mapNo,
          shareUrl: result.shareUrl,
          xySummary: summarizeXy(result.baseXyData),
          hint: "Basemap created. Share the shareUrl with the user for interactive exploration (do not try to plot the map yourself — full coordinates are not returned). Use add_plot to test new embedding batches against this map.",
        };
      }),
  );

  server.registerTool(
    "add_plot",
    {
      title: "Add embeddings to a map (anomaly check)",
      description:
        "Project new embedding CSV file(s) onto an existing basemap and run anomaly detection against the basemap's learned normal area. Preprocessing (L2 normalization, ID columns, dimension names) is inherited from the basemap automatically, so the new file only needs the same embedding dimensionality. Use this to answer: \"is this new batch of embeddings normal compared to the baseline?\" or to track drift over time — coordinates are directly comparable across add_plot calls on the same map. Returns abnormalityStatus (normal/abnormal), scores, a composite diagnostic (normal/warning/danger with distance-from-baseline metrics), and a shareUrl showing the new points overlaid on the basemap.",
      inputSchema: {
        files: filesSchema,
        mapNo: z.number().int().optional()
          .describe("Target basemap number. Defaults to the map most recently created by create_basemap in this session. When unsure, call list_maps and pass the number explicitly."),
        detabn_max_window: z.number().int().optional()
          .describe("Advanced: max window size for sequential abnormality-rate calculation (server default 5). For per-point independent judgment use 1."),
        detabn_rate_threshold: z.number().optional()
          .describe("Advanced: abnormality-rate threshold in (0,1] (server default 1.0 = all points in the window must be outside the normal area)."),
        detabn_threshold: z.number().optional()
          .describe("Advanced: normal-area density threshold (server default 0). A point is normal when its normal-area value exceeds this."),
        ...identnaShape,
      },
    },
    async (args) =>
      runTool("add_plot", async () => {
        const mapNo = args.mapNo ?? api.lastMapNo;
        if (mapNo == null) {
          throw new ToolError(
            "MAP_NO_REQUIRED",
            "No target map: mapNo was not given and no basemap has been created in this server session. Call list_maps, pick the right map (typically the newest embedding basemap, or ask the user), and pass its mapNo explicitly.",
          );
        }
        const result = await api.addplotEmbedding({
          files: args.files,
          mapNo,
          identna: {
            resolution: args.identna_resolution,
            effectiveRadius: args.identna_effective_radius,
            erMethod: args.identna_er_method,
            knnK: args.identna_knn_k,
          },
          detabn: {
            maxWindow: args.detabn_max_window,
            rateThreshold: args.detabn_rate_threshold,
            threshold: args.detabn_threshold,
          },
        });

        const ds = result.diagnosticScore;
        const distance = ds?.distance;
        const perPoint: number[] | undefined = distance?.normalizedDistancesPerPoint;
        const diagnostic = ds
          ? {
              compositeStatus: ds.compositeStatus ?? null,
              statusLegend: "normal = inside baseline | warning = outside normal area but within 2xRg of baseline centroid | danger = outside and far from baseline",
              distance: distance
                ? {
                    normalizedDistance: distance.normalizedDistance ?? null,
                    radiusOfGyration: distance.radiusOfGyration ?? null,
                    exceedanceRatio: distance.exceedanceRatio ?? null,
                    maxPointDeviation: Array.isArray(perPoint) && perPoint.length ? Math.max(...perPoint) : null,
                    note: "normalizedDistance = mean distance of new points from the basemap centroid, in units of the basemap's radius of gyration (Rg); exceedanceRatio = share of new points beyond 2xRg",
                  }
                : null,
            }
          : null;

        return {
          ok: true,
          mapNo,
          addPlotNo: result.addPlotNo,
          nPointsPlotted: result.xyData.length,
          abnormalityStatus: result.abnormalityStatus,
          abnormalityScore: result.abnormalityScore,
          diagnostic,
          xySummary: summarizeXy(result.xyData),
          shareUrl: result.shareUrl,
          hint: "Share the shareUrl with the user to inspect the new points overlaid on the basemap.",
        };
      }),
  );

  server.registerTool(
    "list_maps",
    {
      title: "List toorPIA maps",
      description:
        "List the maps that belong to the configured API key (newest first): mapNo, label, creation date, record count, embedding dimensionality, and shareUrl. Use this to find an existing basemap for add_plot, to check what has already been analyzed, or to verify that authentication works.",
      inputSchema: {
        limit: z.number().int().min(1).max(100).optional()
          .describe("Maximum number of maps to return (default 20, newest first)."),
      },
    },
    async ({ limit }) =>
      runTool("list_maps", async () => {
        const maps = await api.listMaps();
        const sorted = [...maps].sort((a, b) => {
          const ta = a.createdAt ? Date.parse(a.createdAt) : 0;
          const tb = b.createdAt ? Date.parse(b.createdAt) : 0;
          return tb - ta;
        });
        const shown = sorted.slice(0, limit ?? 20).map((m) => ({
          mapNo: m.mapNo,
          label: m.label ?? null,
          tag: m.tag ?? null,
          description: m.description ? String(m.description).slice(0, 120) : null,
          createdAt: m.createdAt ?? null,
          nRecord: m.nRecord ?? null,
          nDimension: m.nDimension ?? null,
          shareUrl: m.shareUrl ?? null,
        }));
        return {
          ok: true,
          totalMaps: maps.length,
          shown: shown.length,
          maps: shown,
        };
      }),
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`[toorpia-mcp] server started (stdio) v${SERVER_VERSION}`);
  console.error(`[toorpia-mcp] API URL: ${apiUrl}`);
  console.error(`[toorpia-mcp] API key: ${process.env.TOORPIA_API_KEY ? "set" : "NOT SET (tools will fail until TOORPIA_API_KEY is configured)"}`);
}
