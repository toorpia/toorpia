import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { toorpiaClient } from "../client/toorpia.js";
import { SplitDF } from "./common.js";

// Logging function
function logTool(name: string, result: "OK" | string, durationMs: number): void {
  const status = result === "OK" ? "OK" : `ERROR:${result}`;
  console.error(`[TOOL] ${name}: ${status} (${durationMs}ms)`);
}

// Fit transform tool for CSV/DataFrame data
async function fitTransform(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { data, ...opts } = args;
    const result = await toorpiaClient.fitTransformSplit({ data, ...opts });
    logTool("fit_transform", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "FIT_TRANSFORM_FAILED",
      reason: error.message
    };
    logTool("fit_transform", "FIT_TRANSFORM_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Addplot tool for CSV/DataFrame data
async function addplot(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { mode = "full", ...rest } = args;
    const result = await toorpiaClient.addplotSplit(rest);
    
    // Handle mode parameter for backward compatibility
    if (mode === "xy") {
      logTool("addplot", "OK", Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result.xyData) }] };
    } else {
      logTool("addplot", "OK", Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  } catch (error: any) {
    const result = {
      ok: false,
      code: "ADDPLOT_FAILED",
      reason: error.message
    };
    logTool("addplot", "ADDPLOT_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// CSV tool definitions
const csvToolDefinitions = [
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
    handler: fitTransform
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
    handler: addplot
  }
];

// CSV tool handlers map
export const csvToolHandlers = new Map<string, (args: any) => Promise<CallToolResult>>();

// Initialize handlers map
for (const toolDef of csvToolDefinitions) {
  csvToolHandlers.set(toolDef.name, toolDef.handler);
}

// Register CSV tools - this will be called from server.ts
export function registerCsvTools(server: Server): void {
  // Tool registration will be handled by the main server setup
  // This function exists for consistency but actual registration happens in server.ts
}

// Export tool definitions for server registration
export function getCsvToolDefinitions() {
  return csvToolDefinitions.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema) as any,
  }));
}
