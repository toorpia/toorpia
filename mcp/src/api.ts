import { readFileSync, existsSync } from "node:fs";
import { basename } from "node:path";
import { gzipSync } from "node:zlib";
import { Blob } from "node:buffer";
import { fetch, Agent, FormData, type Response } from "undici";
import { ToolError } from "./errors.js";

export interface IdentnaParams {
  resolution?: number;
  effectiveRadius?: number | "auto";
  erMethod?: "silverman" | "knn";
  knnK?: number;
}

export interface DetabnParams {
  maxWindow?: number;
  rateThreshold?: number;
  threshold?: number;
}

export interface BasemapResult {
  baseXyData: number[][];
  mapNo: number;
  shareUrl: string | null;
}

export interface AddplotResult {
  xyData: number[][];
  addPlotNo: number | null;
  abnormalityStatus: string | null;
  abnormalityScore: number | null;
  diagnosticScore: any | null;
  shareUrl: string | null;
}

export interface MapInfo {
  mapNo: number;
  label?: string | null;
  tag?: string | null;
  description?: string | null;
  createdAt?: string;
  nRecord?: number;
  nDimension?: number;
  shareUrl?: string | null;
}

// Basemap creation on large embedding sets can take minutes; disable the
// default 5-minute undici header timeout and rely on a generous cap instead.
const LONG_REQUEST_AGENT = new Agent({
  headersTimeout: 30 * 60 * 1000,
  bodyTimeout: 30 * 60 * 1000,
  connectTimeout: 15 * 1000,
});

interface UploadFile {
  path: string;
  content: Buffer;
  uploadName: string;
  compressed: boolean; // compressed by us (eligible for 415 fallback)
}

export class ToorpiaApi {
  private sessionKey: string | null = null;
  /** mapNo of the basemap most recently created through this server process. */
  public lastMapNo: number | null = null;

  constructor(
    private readonly apiUrl: string,
    private readonly apiKey: string | undefined,
  ) {}

  private async login(): Promise<void> {
    if (!this.apiKey) {
      throw new ToolError(
        "AUTH_MISSING",
        "TOORPIA_API_KEY environment variable is not set. Ask the user to add TOORPIA_API_KEY to the MCP server configuration (the \"env\" block of the client's MCP settings) and restart the client.",
      );
    }
    let res: Response;
    try {
      res = await fetch(`${this.apiUrl}/auth/login`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ apiKey: this.apiKey }),
        dispatcher: LONG_REQUEST_AGENT,
      });
    } catch (e: any) {
      throw this.networkError(e);
    }
    if (!res.ok) {
      throw new ToolError(
        "AUTH_FAILED",
        `Authentication with the toorPIA API failed (HTTP ${res.status}). The TOORPIA_API_KEY is most likely invalid or expired. Ask the user to verify the API key in the MCP server configuration. API URL in use: ${this.apiUrl}`,
      );
    }
    const js = (await res.json().catch(() => ({}))) as { sessionKey?: string };
    if (!js.sessionKey) {
      throw new ToolError(
        "AUTH_FAILED",
        `The toorPIA API at ${this.apiUrl} did not return a session key. Ask the user to verify that TOORPIA_API_URL points to a toorPIA API server.`,
      );
    }
    this.sessionKey = js.sessionKey;
  }

  private networkError(e: any): ToolError {
    const detail = e?.cause?.code ?? e?.code ?? e?.message ?? String(e);
    return new ToolError(
      "NETWORK_ERROR",
      `Could not reach the toorPIA API at ${this.apiUrl} (${detail}). Ask the user to verify TOORPIA_API_URL in the MCP server configuration and their network/VPN access to the server.`,
    );
  }

  /**
   * Perform an authenticated request. Re-authenticates and retries once on 401
   * (expired session key).
   */
  private async request(
    path: string,
    build: (sessionKey: string) => { method: string; body?: any; headers?: Record<string, string> },
  ): Promise<Response> {
    if (!this.sessionKey) await this.login();
    for (let attempt = 0; ; attempt++) {
      const { method, body, headers } = build(this.sessionKey!);
      let res: Response;
      try {
        res = await fetch(`${this.apiUrl}${path}`, {
          method,
          body,
          headers: { "session-key": this.sessionKey!, ...headers },
          dispatcher: LONG_REQUEST_AGENT,
        });
      } catch (e: any) {
        throw this.networkError(e);
      }
      if (res.status === 401 && attempt === 0) {
        this.sessionKey = null;
        await this.login();
        continue;
      }
      return res;
    }
  }

  private async apiError(res: Response, context: string, hint: string): Promise<ToolError> {
    let serverMessage = "";
    try {
      const js: any = await res.json();
      serverMessage = js?.message ?? JSON.stringify(js);
    } catch {
      serverMessage = (await res.text().catch(() => "")).slice(0, 300);
    }
    return new ToolError(
      "API_ERROR",
      `${context} failed (HTTP ${res.status}): ${serverMessage || "no error detail from server"}. ${hint}`,
    );
  }

  /**
   * Load local embedding CSV files for upload. Plain .csv files are
   * gzip-compressed to cut transfer size; .csv.gz files are sent as-is.
   */
  private loadFiles(paths: string[], compress: boolean): UploadFile[] {
    return paths.map((p) => {
      if (!existsSync(p)) {
        throw new ToolError(
          "FILE_NOT_FOUND",
          `File not found: ${p}. Use an absolute path. Ask the user for the correct location of the embedding CSV file.`,
        );
      }
      const lower = p.toLowerCase();
      if (!lower.endsWith(".csv") && !lower.endsWith(".csv.gz")) {
        throw new ToolError(
          "UNSUPPORTED_FILE_TYPE",
          `Unsupported file type: ${p}. Only .csv and .csv.gz embedding files are supported. If the data is in another format (npy, parquet, ...), ask the user to export it as CSV (rows = samples, columns = embedding dimensions).`,
        );
      }
      const content = readFileSync(p);
      if (content.length === 0) {
        throw new ToolError("EMPTY_FILE", `File is empty: ${p}. Check that the embedding export completed correctly.`);
      }
      if (lower.endsWith(".csv.gz") || !compress) {
        return { path: p, content, uploadName: basename(p), compressed: false };
      }
      return {
        path: p,
        content: gzipSync(content, { level: 6 }),
        uploadName: `${basename(p)}.gz`,
        compressed: true,
      };
    });
  }

  private buildForm(files: UploadFile[], fields: Record<string, string>): FormData {
    const form = new FormData();
    for (const f of files) {
      form.append("files", new Blob([f.content]), f.uploadName);
    }
    for (const [k, v] of Object.entries(fields)) {
      form.append(k, v);
    }
    return form;
  }

  /**
   * POST embedding files to an endpoint. If the server rejects gzip-compressed
   * CSV with 415 (older backend), transparently retries uncompressed —
   * mirroring the Python client's fallback behavior.
   */
  private async postEmbeddingFiles(
    path: string,
    filePaths: string[],
    fields: Record<string, string>,
  ): Promise<Response> {
    let files = this.loadFiles(filePaths, true);
    let res = await this.request(path, () => ({ method: "POST", body: this.buildForm(files, fields) }));
    if (res.status === 415 && files.some((f) => f.compressed)) {
      console.error("[toorpia-mcp] server does not accept gzip-compressed CSV; retrying uncompressed");
      files = this.loadFiles(filePaths, false);
      res = await this.request(path, () => ({ method: "POST", body: this.buildForm(files, fields) }));
    }
    return res;
  }

  private identnaFields(identna: IdentnaParams): Record<string, string> {
    const params: Record<string, unknown> = {};
    if (identna.resolution !== undefined) params.resolution = Math.trunc(identna.resolution);
    if (identna.effectiveRadius !== undefined) params.effectiveRadius = identna.effectiveRadius;
    if (identna.erMethod !== undefined) params.erMethod = identna.erMethod;
    if (identna.knnK !== undefined) params.knnK = Math.trunc(identna.knnK);
    return Object.keys(params).length ? { identna_params: JSON.stringify(params) } : {};
  }

  async basemapEmbedding(payload: {
    files: string[];
    label?: string;
    tag?: string;
    description?: string;
    l2Normalization?: boolean;
    idColumns?: number;
    identna?: IdentnaParams;
  }): Promise<BasemapResult> {
    const fields: Record<string, string> = {
      label: payload.label ?? "",
      tag: payload.tag ?? "",
      description: payload.description ?? "",
      ...this.identnaFields(payload.identna ?? {}),
    };
    if (payload.l2Normalization !== undefined) {
      fields.l2_normalization = payload.l2Normalization ? "true" : "false";
    }
    if (payload.idColumns !== undefined) {
      fields.id_columns = String(Math.trunc(payload.idColumns));
    }

    const res = await this.postEmbeddingFiles("/data/basemap_embedding", payload.files, fields);
    if (!res.ok) {
      throw await this.apiError(
        res,
        "Basemap creation",
        "If the message mentions file parsing, run preview_csv on the file to check its structure (numeric matrix, optional leading ID columns). If it mentions size limits, the file may be too large for a single upload.",
      );
    }
    const js: any = await res.json();
    const baseXyData: number[][] = js?.resdata?.baseXyData;
    const mapNo: number = js?.resdata?.mapNo;
    if (!Array.isArray(baseXyData) || typeof mapNo !== "number") {
      throw new ToolError(
        "INVALID_RESPONSE",
        `The toorPIA API returned an unexpected response shape for basemap creation. Verify that TOORPIA_API_URL (${this.apiUrl}) points to a server that supports the /data/basemap_embedding endpoint (v1.2.0 or later).`,
      );
    }
    this.lastMapNo = mapNo;
    return { baseXyData, mapNo, shareUrl: js?.shareUrl ?? null };
  }

  async addplotEmbedding(payload: {
    files: string[];
    mapNo: number;
    identna?: IdentnaParams;
    detabn?: DetabnParams;
  }): Promise<AddplotResult> {
    const detabn = payload.detabn ?? {};
    // threshold is only sent when explicitly requested: when omitted, the
    // server lets detabn derive it from its coverage default (0.90), which is
    // smarter than a fixed value. (The Python client always sends 0, which
    // disables that auto-derivation — do not copy that behavior.)
    const detabnOptions: Record<string, unknown> = {
      maxWindow: Math.trunc(detabn.maxWindow ?? 5),
      rateThreshold: detabn.rateThreshold ?? 1.0,
      printScore: true,
    };
    if (detabn.threshold !== undefined) detabnOptions.threshold = detabn.threshold;
    const fields: Record<string, string> = {
      mapNo: String(payload.mapNo),
      detabn_options: JSON.stringify(detabnOptions),
    };
    const identna = this.identnaFields(payload.identna ?? {});
    if (identna.identna_params) fields.identna_options = identna.identna_params;

    const res = await this.postEmbeddingFiles("/data/addplot_embedding", payload.files, fields);
    if (!res.ok) {
      throw await this.apiError(
        res,
        "Add-plot",
        `If the message mentions a process-method mismatch, map ${payload.mapNo} was not created from embeddings — use list_maps to pick a map created by create_basemap. If it mentions a dimension mismatch, the new CSV must have exactly the same number of embedding dimensions as the basemap (run preview_csv on both files to compare).`,
      );
    }
    const js: any = await res.json();
    const xyData: number[][] = Array.isArray(js?.resdata) ? js.resdata : [];
    return {
      xyData,
      addPlotNo: js?.addPlotNo ?? null,
      abnormalityStatus: js?.abnormalityStatus ?? null,
      abnormalityScore: js?.abnormalityScore ?? null,
      diagnosticScore: js?.diagnosticScore ?? null,
      shareUrl: js?.shareUrl ?? null,
    };
  }

  async listMaps(): Promise<MapInfo[]> {
    const res = await this.request("/maps", () => ({ method: "GET" }));
    if (!res.ok) {
      throw await this.apiError(res, "Listing maps", "Retry once; if it keeps failing, the toorPIA API server may be unavailable.");
    }
    const js: any = await res.json();
    if (!Array.isArray(js)) {
      throw new ToolError(
        "INVALID_RESPONSE",
        `The toorPIA API returned an unexpected response for GET /maps. Verify that TOORPIA_API_URL (${this.apiUrl}) points to a toorPIA API server.`,
      );
    }
    return js as MapInfo[];
  }
}
