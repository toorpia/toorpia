import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { toorpiaClient } from "../client/toorpia.js";

// Check if WAV functionality is enabled
const ENABLE_WAV = process.env.ENABLE_WAV !== "false";

// Logging function
function logTool(name: string, result: "OK" | string, durationMs: number): void {
  const status = result === "OK" ? "OK" : `ERROR:${result}`;
  console.error(`[TOOL] ${name}: ${status} (${durationMs}ms)`);
}

// Not implemented response for disabled WAV functionality
function notImplementedResponse(toolName: string): CallToolResult {
  return { 
    content: [{ 
      type: "text", 
      text: JSON.stringify({
        ok: false, 
        code: "NOT_IMPLEMENTED", 
        reason: `WAV workflow is disabled. Set ENABLE_WAV=true in .env to enable ${toolName}` 
      })
    }] 
  };
}

// Fit transform waveform tool for WAV files
async function fitTransformWaveform(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  
  if (!ENABLE_WAV) {
    logTool("fit_transform_waveform", "NOT_IMPLEMENTED", Date.now() - startTime);
    return notImplementedResponse("fit_transform_waveform");
  }

  try {
    const result = await toorpiaClient.fitTransformWaveform(args);
    logTool("fit_transform_waveform", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "FIT_TRANSFORM_WAVEFORM_FAILED",
      reason: error.message
    };
    logTool("fit_transform_waveform", "FIT_TRANSFORM_WAVEFORM_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// Addplot waveform tool for WAV files
async function addplotWaveform(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  
  if (!ENABLE_WAV) {
    logTool("addplot_waveform", "NOT_IMPLEMENTED", Date.now() - startTime);
    return notImplementedResponse("addplot_waveform");
  }

  try {
    const result = await toorpiaClient.addplotWaveform(args);
    logTool("addplot_waveform", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = {
      ok: false,
      code: "ADDPLOT_WAVEFORM_FAILED",
      reason: error.message
    };
    logTool("addplot_waveform", "ADDPLOT_WAVEFORM_FAILED", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// WAV tool definitions
const wavToolDefinitions = [
  {
    name: "fit_transform_waveform",
    description: "Create a base map from WAV/CSV files. Returns xyData and mapNo. (Requires ENABLE_WAV=true)",
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
      description: z.string().optional()
    }),
    handler: fitTransformWaveform
  },
  {
    name: "addplot_waveform",
    description: "Add WAV/CSV files to an existing map. Returns xyData with abnormality information. (Requires ENABLE_WAV=true)",
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
      detabn_print_score: z.boolean().optional()
    }),
    handler: addplotWaveform
  }
];

// WAV tool handlers map
export const wavToolHandlers = new Map<string, (args: any) => Promise<CallToolResult>>();

// Initialize handlers map
for (const toolDef of wavToolDefinitions) {
  wavToolHandlers.set(toolDef.name, toolDef.handler);
}

// Register WAV tools - this will be called from server.ts
export function registerWavTools(server: Server): void {
  // Tool registration will be handled by the main server setup
  // This function exists for consistency but actual registration happens in server.ts
}

// Export tool definitions for server registration
export function getWavToolDefinitions() {
  return wavToolDefinitions.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: zodToJsonSchema(tool.inputSchema) as any,
  }));
}

// Export ENABLE_WAV status for use in prompts
export { ENABLE_WAV };
