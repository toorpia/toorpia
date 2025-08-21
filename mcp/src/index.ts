// toorpia-mcp-server.ts
// -----------------------------------------------------------------------------
// A minimal MCP server that wraps toorPIA API endpoints as MCP tools.
// - Implements auth using TOORPIA_API_KEY and optional TOORPIA_API_URL
// - Exposes sklearn-like fit_transform (returns ndarray-style data) and
//   addplot with two return modes: "xy" (NumPy-like) or "full" (dict-like)
// - Also provides list_map, list_addplots, get_addplot, get_addplot_features
//
// Run (Node >= 18):
//   npm i -D typescript ts-node @types/node
//   npm i @modelcontextprotocol/sdk zod undici
//   npx ts-node toorpia-mcp-server.ts
//   (or compile with tsc)
//
// In Claude Desktop / MCP Inspector, register as a stdio server:
//   command: node
//   args: ["./toorpia-mcp-server.js"]  (after tsc) or ["./toorpia-mcp-server.ts"] with ts-node
//
// Env vars required:
//   TOORPIA_API_KEY=<your key>
//   TOORPIA_API_URL=<http://host:port>  (optional; defaults to http://localhost:3000)
// -----------------------------------------------------------------------------

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  ListToolsRequestSchema, 
  CallToolRequestSchema,
  ListToolsResult,
  CallToolResult
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import * as fs from "fs";
import * as path from "path";

// Use fetch from undici on Node<18 if needed
import "undici";

// ----------------------------- Helpers --------------------------------------

const API_URL = process.env.TOORPIA_API_URL ?? "http://localhost:3000";
const API_KEY = process.env.TOORPIA_API_KEY ?? "";

class ToorPIAClient {
  private sessionKey: string | null = null;
  public mapNo: number | null = null;
  public shareUrl: string | null = null;
  public currentAddPlotNo: number | null = null;

  constructor(private apiUrl: string, private apiKey: string) {}

  private async ensureAuth(): Promise<void> {
    if (this.sessionKey) return;
    if (!this.apiKey) throw new Error("TOORPIA_API_KEY is not set");
    const res = await fetch(`${this.apiUrl}/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ apiKey: this.apiKey }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`Auth failed: ${res.status} ${t}`);
    }
    const js = (await res.json()) as { sessionKey?: string };
    if (!js.sessionKey) throw new Error("No sessionKey in auth response");
    this.sessionKey = js.sessionKey;
  }

  private headersJSON(): HeadersInit {
    if (!this.sessionKey) throw new Error("Not authenticated");
    return { "content-type": "application/json", "session-key": this.sessionKey };
  }

  // fit_transform for DataFrame-like input in pandas orient="split"
  async fitTransformSplit(payload: {
    data: { columns: string[]; index?: (number | string)[]; data: (number | null)[][] };
    label?: string; tag?: string; description?: string;
    random_seed?: number;
    weight_option_str?: string; type_option_str?: string;
    identna_resolution?: number; identna_effective_radius?: number;
  }): Promise<{ xyData: number[][]; mapNo: number; shareUrl?: string }>{
    await this.ensureAuth();
    const {
      data,
      label, tag, description,
      random_seed,
      weight_option_str, type_option_str,
      identna_resolution, identna_effective_radius,
    } = payload;

    const body: any = {
      ...data,
      label, tag, description,
      weight_option_str: weight_option_str ?? null,
      type_option_str: type_option_str ?? null,
    };
    if (typeof random_seed === "number" && random_seed !== 42) body.randomSeed = random_seed;
    const identna: any = {};
    if (typeof identna_resolution === "number") identna.resolution = identna_resolution;
    if (typeof identna_effective_radius === "number") identna.effectiveRadius = identna_effective_radius;
    if (Object.keys(identna).length) body.identnaParams = identna;

    const res = await fetch(`${this.apiUrl}/data/fit_transform`, {
      method: "POST", headers: this.headersJSON(), body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`fit_transform failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const baseXyData: number[][] = js?.resdata?.baseXyData ?? [];
    const mapNo: number = js?.resdata?.mapNo;
    this.mapNo = mapNo;
    this.shareUrl = js?.shareUrl ?? null;
    return { xyData: baseXyData, mapNo, shareUrl: this.shareUrl ?? undefined };
  }

  // addplot for DataFrame-like input (orient split)
  async addplotSplit(payload: {
    data: { columns: string[]; index?: (number | string)[]; data: (number | null)[][] };
    mapNo?: number;
    weight_option_str?: string; type_option_str?: string;
    detabn_max_window?: number; detabn_rate_threshold?: number; detabn_threshold?: number; detabn_print_score?: boolean;
  }): Promise<{ xyData: number[][]; addPlotNo?: number; abnormalityStatus?: string | null; abnormalityScore?: number | null; shareUrl?: string }>{
    await this.ensureAuth();
    const {
      data, mapNo,
      weight_option_str, type_option_str,
      detabn_max_window, detabn_rate_threshold, detabn_threshold, detabn_print_score
    } = payload;

    const body: any = { ...data };
    if (this.mapNo && !mapNo) body.mapNo = this.mapNo; else if (mapNo) body.mapNo = mapNo;
    if (!body.mapNo) throw new Error("mapNo is required (call fit_transform first or provide mapNo)");

    body.weight_option_str = weight_option_str ?? null;
    body.type_option_str = type_option_str ?? null;

    if (typeof detabn_max_window === "number") body.detabn_max_window = detabn_max_window;
    if (typeof detabn_rate_threshold === "number") body.detabn_rate_threshold = detabn_rate_threshold;
    if (typeof detabn_threshold === "number") body.detabn_threshold = detabn_threshold;
    if (typeof detabn_print_score === "boolean") body.detabn_print_score = detabn_print_score;

    const res = await fetch(`${this.apiUrl}/data/addplot`, {
      method: "POST", headers: this.headersJSON(), body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`addplot failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const addXyData: number[][] = js?.resdata ?? [];
    this.currentAddPlotNo = js?.addPlotNo ?? null;
    this.shareUrl = js?.shareUrl ?? null;
    return {
      xyData: addXyData,
      addPlotNo: this.currentAddPlotNo ?? undefined,
      abnormalityStatus: js?.abnormalityStatus ?? null,
      abnormalityScore: js?.abnormalityScore ?? null,
      shareUrl: this.shareUrl ?? undefined,
    };
  }

  async listMap(): Promise<any> {
    await this.ensureAuth();
    const res = await fetch(`${this.apiUrl}/maps`, { headers: this.headersJSON() });
    if (!res.ok) throw new Error(`list_map failed: ${res.status} ${await res.text()}`);
    return await res.json();
  }

  async listAddplots(mapNo: number): Promise<any> {
    await this.ensureAuth();
    const res = await fetch(`${this.apiUrl}/maps/${mapNo}/addplots`, { headers: this.headersJSON() });
    if (!res.ok) throw new Error(`list_addplots failed: ${res.status} ${await res.text()}`);
    return await res.json();
  }

  async getAddplot(mapNo: number, addplotNo: number): Promise<{ addPlot: any; xyData: number[][]; shareUrl?: string }> {
    await this.ensureAuth();
    const res = await fetch(`${this.apiUrl}/maps/${mapNo}/addplots/${addplotNo}`, { headers: this.headersJSON() });
    if (!res.ok) throw new Error(`get_addplot failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    this.shareUrl = js?.shareUrl ?? null;
    const xyData: number[][] = js?.xyData ?? [];
    return { addPlot: js?.addPlot, xyData, shareUrl: this.shareUrl ?? undefined };
  }

  async getAddplotFeatures(mapNo: number, addplotNo: number, use_tscore?: boolean): Promise<any> {
    await this.ensureAuth();
    const url = new URL(`${this.apiUrl}/maps/${mapNo}/addplots/${addplotNo}/features`);
    if (use_tscore) url.searchParams.set("tscore", "true");
    const res = await fetch(url, { headers: this.headersJSON() });
    if (!res.ok) throw new Error(`get_addplot_features failed: ${res.status} ${await res.text()}`);
    return await res.json();
  }

  // fit_transform_waveform for WAV/CSV files
  async fitTransformWaveform(payload: {
    files: string[];
    mkfftseg_di?: number; mkfftseg_hp?: number; mkfftseg_lp?: number;
    mkfftseg_nm?: number; mkfftseg_ol?: number; mkfftseg_sr?: number;
    mkfftseg_wf?: string; mkfftseg_wl?: number;
    identna_resolution?: number; identna_effective_radius?: number;
    label?: string; tag?: string; description?: string;
  }): Promise<{ xyData: number[][]; mapNo: number; shareUrl?: string }> {
    await this.ensureAuth();
    const {
      files,
      mkfftseg_di = 1, mkfftseg_hp = -1.0, mkfftseg_lp = -1.0,
      mkfftseg_nm = 0, mkfftseg_ol = 50.0, mkfftseg_sr = 48000,
      mkfftseg_wf = "hanning", mkfftseg_wl = 65536,
      identna_resolution, identna_effective_radius,
      label = "", tag = "", description = ""
    } = payload;

    const formData = new FormData();
    
    // Add files
    for (const filePath of files) {
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }
      const fileContent = fs.readFileSync(filePath);
      const fileName = path.basename(filePath);
      formData.append('files', new Blob([fileContent]), fileName);
    }

    // Add parameters
    const mkfftsegOptions = {
      di: mkfftseg_di, hp: mkfftseg_hp, lp: mkfftseg_lp,
      nm: mkfftseg_nm, ol: mkfftseg_ol, sr: mkfftseg_sr,
      wf: mkfftseg_wf, wl: mkfftseg_wl
    };
    
    const identnaOptions: any = {};
    if (typeof identna_resolution === "number") identnaOptions.resolution = identna_resolution;
    if (typeof identna_effective_radius === "number") identnaOptions.effectiveRadius = identna_effective_radius;

    formData.append('mkfftseg_options', JSON.stringify(mkfftsegOptions));
    formData.append('identna_options', JSON.stringify(identnaOptions));
    formData.append('label', label);
    formData.append('tag', tag);
    formData.append('description', description);

    const headers = { 'session-key': this.sessionKey! };
    const res = await fetch(`${this.apiUrl}/data/fit_transform_waveform`, {
      method: 'POST', headers, body: formData
    });
    
    if (!res.ok) throw new Error(`fit_transform_waveform failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const baseXyData: number[][] = js?.resdata?.baseXyData ?? [];
    const mapNo: number = js?.resdata?.mapNo;
    this.mapNo = mapNo;
    this.shareUrl = js?.shareUrl ?? null;
    return { xyData: baseXyData, mapNo, shareUrl: this.shareUrl ?? undefined };
  }

  // addplot_waveform for WAV/CSV files
  async addplotWaveform(payload: {
    files: string[]; mapNo?: number;
    mkfftseg_di?: number; mkfftseg_hp?: number; mkfftseg_lp?: number;
    mkfftseg_nm?: number; mkfftseg_ol?: number; mkfftseg_sr?: number;
    mkfftseg_wf?: string; mkfftseg_wl?: number;
    detabn_max_window?: number; detabn_rate_threshold?: number;
    detabn_threshold?: number; detabn_print_score?: boolean;
  }): Promise<{ xyData: number[][]; addPlotNo?: number; abnormalityStatus?: string | null; abnormalityScore?: number | null; shareUrl?: string }> {
    await this.ensureAuth();
    const {
      files, mapNo,
      mkfftseg_di = 1, mkfftseg_hp = -1.0, mkfftseg_lp = -1.0,
      mkfftseg_nm = 0, mkfftseg_ol = 50.0, mkfftseg_sr = 48000,
      mkfftseg_wf = "hanning", mkfftseg_wl = 65536,
      detabn_max_window = 5, detabn_rate_threshold = 1.0,
      detabn_threshold = 0, detabn_print_score = true
    } = payload;

    const targetMapNo = mapNo ?? this.mapNo;
    if (!targetMapNo) throw new Error("mapNo is required (call fit_transform first or provide mapNo)");

    const formData = new FormData();
    
    // Add files
    for (const filePath of files) {
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }
      const fileContent = fs.readFileSync(filePath);
      const fileName = path.basename(filePath);
      formData.append('files', new Blob([fileContent]), fileName);
    }

    // Add parameters
    const mkfftsegOptions = {
      di: mkfftseg_di, hp: mkfftseg_hp, lp: mkfftseg_lp,
      nm: mkfftseg_nm, ol: mkfftseg_ol, sr: mkfftseg_sr,
      wf: mkfftseg_wf, wl: mkfftseg_wl
    };
    
    const detabnOptions = {
      maxWindow: detabn_max_window, rateThreshold: detabn_rate_threshold,
      threshold: detabn_threshold, printScore: detabn_print_score
    };

    formData.append('mapNo', targetMapNo.toString());
    formData.append('mkfftseg_options', JSON.stringify(mkfftsegOptions));
    formData.append('detabn_options', JSON.stringify(detabnOptions));

    const headers = { 'session-key': this.sessionKey! };
    const res = await fetch(`${this.apiUrl}/data/addplot_waveform`, {
      method: 'POST', headers, body: formData
    });
    
    if (!res.ok) throw new Error(`addplot_waveform failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const addXyData: number[][] = js?.resdata ?? [];
    this.currentAddPlotNo = js?.addPlotNo ?? null;
    this.shareUrl = js?.shareUrl ?? null;
    return {
      xyData: addXyData,
      addPlotNo: this.currentAddPlotNo ?? undefined,
      abnormalityStatus: js?.abnormalityStatus ?? null,
      abnormalityScore: js?.abnormalityScore ?? null,
      shareUrl: this.shareUrl ?? undefined,
    };
  }

  // export_map (download_map)
  async exportMap(mapNo: number, exportDir: string): Promise<any> {
    await this.ensureAuth();
    const res = await fetch(`${this.apiUrl}/maps/export/${mapNo}`, {
      headers: { 'session-key': this.sessionKey! }
    });
    
    if (!res.ok) throw new Error(`export_map failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const mapData = js?.mapData ?? {};
    this.shareUrl = js?.shareUrl ?? null;

    // Create export directory if it doesn't exist
    if (!fs.existsSync(exportDir)) {
      fs.mkdirSync(exportDir, { recursive: true });
    }

    // Save all files from mapData
    for (const [filename, fileContentB64] of Object.entries(mapData)) {
      try {
        const fileContent = Buffer.from(fileContentB64 as string, 'base64').toString('utf-8');
        const filePath = path.join(exportDir, filename);
        fs.writeFileSync(filePath, fileContent, 'utf-8');
      } catch (e) {
        throw new Error(`Error saving file ${filename}: ${e}`);
      }
    }

    return { mapData, shareUrl: this.shareUrl, exportPath: exportDir };
  }

  // import_map (upload_map)
  async importMap(inputDir: string): Promise<number> {
    await this.ensureAuth();
    
    if (!fs.existsSync(inputDir)) {
      throw new Error(`Directory not found: ${inputDir}`);
    }

    const mapData: { [filename: string]: string } = {};
    const files = fs.readdirSync(inputDir);
    
    // Read all files (excluding add plot and log files)
    for (const filename of files) {
      if (filename.startsWith('segments-add-') || 
          filename.startsWith('xy-add-') || 
          filename.startsWith('rawdata_add_') || 
          filename.endsWith('.log')) {
        continue;
      }
      
      const filePath = path.join(inputDir, filename);
      if (fs.statSync(filePath).isFile()) {
        const fileContent = fs.readFileSync(filePath);
        mapData[filename] = Buffer.from(fileContent).toString('base64');
      }
    }

    const res = await fetch(`${this.apiUrl}/maps/import`, {
      method: 'POST',
      headers: this.headersJSON(),
      body: JSON.stringify({ mapData })
    });

    if (!res.ok) throw new Error(`import_map failed: ${res.status} ${await res.text()}`);
    const js = await res.json();
    const newMapNo = js?.mapNo;
    this.shareUrl = js?.shareUrl ?? null;
    return newMapNo;
  }
}

// --------------------------- MCP server setup --------------------------------

const server = new Server({ name: "toorpia-mcp", version: "1.0.0" });
const client = new ToorPIAClient(API_URL, API_KEY);

// Schema for DataFrame (pandas orient="split")
const SplitDF = z.object({
  columns: z.array(z.string()),
  index: z.array(z.union([z.number(), z.string()])).optional(),
  data: z.array(z.array(z.number().nullable())),
});

// Define tool schemas
const toolDefinitions = [
  {
    name: "fit_transform",
    description: "Create a base map from a DataFrame (pandas orient='split'). Returns xyData and mapNo.",
    inputSchema: z.object({
      data: SplitDF,
      label: z.string().optional(),
      tag: z.string().optional(),
      description: z.string().optional(),
      random_seed: z.number().optional(),
      weight_option_str: z.string().optional(),
      type_option_str: z.string().optional(),
      identna_resolution: z.number().optional(),
      identna_effective_radius: z.number().optional(),
    }),
  },
  {
    name: "addplot",
    description: "Add data to an existing map. mode='xy' returns only xyData; mode='full' returns dict-like payload (default: full).",
    inputSchema: z.object({
      data: SplitDF,
      mapNo: z.number().optional(),
      weight_option_str: z.string().optional(),
      type_option_str: z.string().optional(),
      detabn_max_window: z.number().optional(),
      detabn_rate_threshold: z.number().optional(),
      detabn_threshold: z.number().optional(),
      detabn_print_score: z.boolean().optional(),
      mode: z.enum(["xy", "full"]).optional(),
    }),
  },
  {
    name: "list_map",
    description: "List maps bound to this API key",
    inputSchema: z.object({}),
  },
  {
    name: "list_addplots",
    description: "List addplots for a map",
    inputSchema: z.object({ mapNo: z.number() }),
  },
  {
    name: "get_addplot",
    description: "Get a specific addplot (returns metadata + xyData)",
    inputSchema: z.object({ mapNo: z.number(), addplotNo: z.number() }),
  },
  {
    name: "get_addplot_features",
    description: "Get features for an addplot (zscore by default; set use_tscore=true for t-score)",
    inputSchema: z.object({ mapNo: z.number(), addplotNo: z.number(), use_tscore: z.boolean().optional() }),
  },
  {
    name: "fit_transform_waveform",
    description: "Create a base map from WAV/CSV files. Returns xyData and mapNo.",
    inputSchema: z.object({
      files: z.array(z.string()),
      mkfftseg_di: z.number().optional(),
      mkfftseg_hp: z.number().optional(),
      mkfftseg_lp: z.number().optional(),
      mkfftseg_nm: z.number().optional(),
      mkfftseg_ol: z.number().optional(),
      mkfftseg_sr: z.number().optional(),
      mkfftseg_wf: z.string().optional(),
      mkfftseg_wl: z.number().optional(),
      identna_resolution: z.number().optional(),
      identna_effective_radius: z.number().optional(),
      label: z.string().optional(),
      tag: z.string().optional(),
      description: z.string().optional(),
    }),
  },
  {
    name: "addplot_waveform",
    description: "Add WAV/CSV files to an existing map. Returns xyData with abnormality information.",
    inputSchema: z.object({
      files: z.array(z.string()),
      mapNo: z.number().optional(),
      mkfftseg_di: z.number().optional(),
      mkfftseg_hp: z.number().optional(),
      mkfftseg_lp: z.number().optional(),
      mkfftseg_nm: z.number().optional(),
      mkfftseg_ol: z.number().optional(),
      mkfftseg_sr: z.number().optional(),
      mkfftseg_wf: z.string().optional(),
      mkfftseg_wl: z.number().optional(),
      detabn_max_window: z.number().optional(),
      detabn_rate_threshold: z.number().optional(),
      detabn_threshold: z.number().optional(),
      detabn_print_score: z.boolean().optional(),
    }),
  },
  {
    name: "export_map",
    description: "Export a map to a directory. Returns map data and export path.",
    inputSchema: z.object({
      mapNo: z.number(),
      exportDir: z.string(),
    }),
  },
  {
    name: "import_map",
    description: "Import a map from a directory. Returns new mapNo.",
    inputSchema: z.object({
      inputDir: z.string(),
    }),
  },
  {
    name: "whoami",
    description: "Verify authentication and show current session status",
    inputSchema: z.object({}),
  },
];

// Handle tools/list requests
server.setRequestHandler(ListToolsRequestSchema, async (): Promise<ListToolsResult> => {
  return {
    tools: toolDefinitions.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: zodToJsonSchema(tool.inputSchema) as any,
    })),
  };
});

// Handle tools/call requests
server.setRequestHandler(CallToolRequestSchema, async (request): Promise<CallToolResult> => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case "fit_transform": {
        const { data, ...opts } = args as any;
        const r = await client.fitTransformSplit({ data, ...opts });
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "addplot": {
        const { mode = "full", ...rest } = args as any;
        const r = await client.addplotSplit(rest);
        if (mode === "xy") return { content: [{ type: "text", text: JSON.stringify(r.xyData) }] };
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "list_map": {
        const r = await client.listMap();
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "list_addplots": {
        const { mapNo } = args as any;
        const r = await client.listAddplots(mapNo);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "get_addplot": {
        const { mapNo, addplotNo } = args as any;
        const r = await client.getAddplot(mapNo, addplotNo);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "get_addplot_features": {
        const { mapNo, addplotNo, use_tscore } = args as any;
        const r = await client.getAddplotFeatures(mapNo, addplotNo, use_tscore);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "fit_transform_waveform": {
        const r = await client.fitTransformWaveform(args as any);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "addplot_waveform": {
        const r = await client.addplotWaveform(args as any);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "export_map": {
        const { mapNo, exportDir } = args as any;
        const r = await client.exportMap(mapNo, exportDir);
        return { content: [{ type: "text", text: JSON.stringify(r) }] };
      }
      
      case "import_map": {
        const { inputDir } = args as any;
        const newMapNo = await client.importMap(inputDir);
        return { content: [{ type: "text", text: JSON.stringify({ mapNo: newMapNo }) }] };
      }
      
      case "whoami": {
        try {
          await client.listMap();
          return { content: [{ type: "text", text: `OK: session active. API_URL=${API_URL}` }] };
        } catch (e: any) {
          return { content: [{ type: "text", text: `NG: ${e.message}` }] };
        }
      }
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// start server -----------------------------------------------------------------
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("toorpia-mcp server started (stdio). API_URL=", API_URL);
