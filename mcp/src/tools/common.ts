import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolResult, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import * as fs from "fs";
import * as path from "path";
import { toorpiaClient } from "../client/toorpia.js";
import { FileLocationResponse, FileTypeResponse } from "../types.js";

// Logging function
function logTool(name: string, result: "OK" | string, durationMs: number): void {
  const status = result === "OK" ? "OK" : `ERROR:${result}`;
  console.error(`[TOOL] ${name}: ${status} (${durationMs}ms)`);
}

// Schema for DataFrame (pandas orient="split")
export const SplitDF = z.object({
  columns: z.array(z.string()),
  index: z.array(z.union([z.number(), z.string()])).optional(),
  data: z.array(z.array(z.number().nullable())),
});

// Locate file tool
async function locateFile(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { baseDir, path: filePath } = args;
    const resolvedPath = baseDir ? path.resolve(baseDir, filePath) : path.resolve(filePath);
    const exists = fs.existsSync(resolvedPath);
    
    const result: FileLocationResponse = {
      ok: true,
      absPath: resolvedPath,
      exists
    };
    
    logTool("locate_file", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result: FileLocationResponse = {
      ok: false,
      code: "LOCATE_ERROR",
      reason: error.message
    };
    logTool("locate_file", "LOCATE_ERROR", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Detect file type tool
async function detectFileType(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { path: filePath } = args;
    const resolvedPath = path.resolve(filePath);
    
    if (!fs.existsSync(resolvedPath)) {
      const result: FileTypeResponse = {
        ok: false,
        code: "FILE_NOT_FOUND",
        reason: `File does not exist: ${resolvedPath}`
      };
      logTool("detect_file_type", "FILE_NOT_FOUND", Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const ext = path.extname(resolvedPath).toLowerCase();
    let kind: "csv" | "wav" | "unknown" = "unknown";
    let reason = "";

    if (ext === ".csv") {
      kind = "csv";
      reason = "Detected CSV by extension";
    } else if (ext === ".wav") {
      try {
        // Check for RIFF header in WAV files
        const buffer = fs.readFileSync(resolvedPath);
        const header = buffer.slice(0, 4).toString('ascii');
        const isWav = header === 'RIFF';
        if (isWav) {
          kind = "wav";
          reason = "Detected WAV by RIFF header";
        } else {
          reason = "File has .wav extension but no RIFF header";
        }
      } catch (e) {
        reason = `File has .wav extension but could not read header: ${e}`;
      }
    } else {
      reason = `Unknown file type with extension: ${ext}`;
    }

    const result: FileTypeResponse = {
      ok: true,
      kind,
      reason
    };

    logTool("detect_file_type", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result: FileTypeResponse = {
      ok: false,
      code: "DETECT_ERROR",
      reason: error.message
    };
    logTool("detect_file_type", "DETECT_ERROR", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Whoami tool
async function whoami(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    await toorpiaClient.listMap();
    const result = { 
      ok: true, 
      message: `OK: session active. API_URL=${process.env.TOORPIA_API_URL ?? "http://localhost:3000"}` 
    };
    logTool("whoami", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "AUTH_FAILED", 
      reason: error.message
    };
    logTool("whoami", "AUTH_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// List map tool
async function listMap(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const result = await toorpiaClient.listMap();
    logTool("list_map", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "LIST_MAP_FAILED",
      reason: error.message
    };
    logTool("list_map", "LIST_MAP_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// List addplots tool
async function listAddplots(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { mapNo } = args;
    const result = await toorpiaClient.listAddplots(mapNo);
    logTool("list_addplots", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "LIST_ADDPLOTS_FAILED",
      reason: error.message
    };
    logTool("list_addplots", "LIST_ADDPLOTS_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Get addplot tool
async function getAddplot(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { mapNo, addplotNo } = args;
    const result = await toorpiaClient.getAddplot(mapNo, addplotNo);
    logTool("get_addplot", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "GET_ADDPLOT_FAILED",
      reason: error.message
    };
    logTool("get_addplot", "GET_ADDPLOT_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Get addplot features tool
async function getAddplotFeatures(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { mapNo, addplotNo, use_tscore } = args;
    const result = await toorpiaClient.getAddplotFeatures(mapNo, addplotNo, use_tscore);
    logTool("get_addplot_features", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "GET_ADDPLOT_FEATURES_FAILED",
      reason: error.message
    };
    logTool("get_addplot_features", "GET_ADDPLOT_FEATURES_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Export map tool
async function exportMap(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { mapNo, exportDir } = args;
    const result = await toorpiaClient.exportMap(mapNo, exportDir);
    logTool("export_map", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "EXPORT_MAP_FAILED",
      reason: error.message
    };
    logTool("export_map", "EXPORT_MAP_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Import map tool
async function importMap(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { inputDir } = args;
    const newMapNo = await toorpiaClient.importMap(inputDir);
    const result = { mapNo: newMapNo };
    logTool("import_map", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "IMPORT_MAP_FAILED",
      reason: error.message
    };
    logTool("import_map", "IMPORT_MAP_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Tool definitions
const commonToolDefinitions = [
  {
    name: "locate_file",
    description: "Locate and check existence of a file. Returns absolute path and existence status.",
    inputSchema: z.object({
      baseDir: z.string().optional(),
      path: z.string()
    }),
    handler: locateFile
  },
  {
    name: "detect_file_type", 
    description: "Detect file type (CSV/WAV/unknown). Checks extension and content headers.",
    inputSchema: z.object({
      path: z.string()
    }),
    handler: detectFileType
  },
  {
    name: "whoami",
    description: "Verify authentication and show current session status",
    inputSchema: z.object({}),
    handler: whoami
  },
  {
    name: "list_map",
    description: "List maps bound to this API key",
    inputSchema: z.object({}),
    handler: listMap
  },
  {
    name: "list_addplots",
    description: "List addplots for a map",
    inputSchema: z.object({ mapNo: z.number() }),
    handler: listAddplots
  },
  {
    name: "get_addplot",
    description: "Get a specific addplot (returns metadata + xyData)",
    inputSchema: z.object({ mapNo: z.number(), addplotNo: z.number() }),
    handler: getAddplot
  },
  {
    name: "get_addplot_features",
    description: "Get features for an addplot (zscore by default; set use_tscore=true for t-score)",
    inputSchema: z.object({ mapNo: z.number(), addplotNo: z.number(), use_tscore: z.boolean().optional() }),
    handler: getAddplotFeatures
  },
  {
    name: "export_map",
    description: "Export a map to a directory. Returns map data and export path.",
    inputSchema: z.object({
      mapNo: z.number(),
      exportDir: z.string(),
    }),
    handler: exportMap
  },
  {
    name: "import_map",
    description: "Import a map from a directory. Returns new mapNo.",
    inputSchema: z.object({
      inputDir: z.string(),
    }),
    handler: importMap
  }
];

// Common tool handlers map
export const commonToolHandlers = new Map<string, (args: any) => Promise<CallToolResult>>();

// Initialize handlers map
for (const toolDef of commonToolDefinitions) {
  commonToolHandlers.set(toolDef.name, toolDef.handler);
}

// Register common tools - this will be called from server.ts
export function registerCommonTools(server: Server): void {
  // Tool registration will be handled by the main server setup
  // This function exists for consistency but actual registration happens in server.ts
}

// Export tool definitions for server registration
export function getCommonToolDefinitions() {
  return commonToolDefinitions.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema) as any,
  }));
}
