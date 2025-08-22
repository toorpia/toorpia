import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  ListToolsRequestSchema, 
  CallToolRequestSchema,
  ListToolsResult,
  CallToolResult
} from "@modelcontextprotocol/sdk/types.js";

// Import tool modules
import { getCommonToolDefinitions, commonToolHandlers } from "./tools/common.js";
import { getCsvToolDefinitions, csvToolHandlers } from "./tools/csv.js";
import { getWavToolDefinitions, wavToolHandlers } from "./tools/wav.js";

// Import prompt modules
import { registerWorkflowCsvPrompt } from "./prompts/workflow_csv.js";
import { registerWorkflowWavPrompt } from "./prompts/workflow_wav.js";

// Create server instance
const server = new Server({ name: "toorpia-mcp", version: "1.0.0" });

// Combine all tool definitions
const allToolDefinitions = [
  ...getCommonToolDefinitions(),
  ...getCsvToolDefinitions(),
  ...getWavToolDefinitions(),
];

// Combine all tool handlers
const allToolHandlers = new Map([
  ...commonToolHandlers,
  ...csvToolHandlers,
  ...wavToolHandlers,
]);

// Register tools/list handler
server.setRequestHandler(ListToolsRequestSchema, async (): Promise<ListToolsResult> => {
  return {
    tools: allToolDefinitions,
  };
});

// Register tools/call handler
server.setRequestHandler(CallToolRequestSchema, async (request): Promise<CallToolResult> => {
  const { name, arguments: args } = request.params;
  
  const handler = allToolHandlers.get(name);
  if (!handler) {
    return {
      content: [{ 
        type: "text", 
        text: JSON.stringify({
          ok: false,
          code: "UNKNOWN_TOOL",
          reason: `Unknown tool: ${name}`
        })
      }],
      isError: true,
    };
  }

  try {
    return await handler(args);
  } catch (error: any) {
    return {
      content: [{ 
        type: "text", 
        text: JSON.stringify({
          ok: false,
          code: "TOOL_EXECUTION_ERROR",
          reason: `Tool execution failed: ${error.message}`
        })
      }],
      isError: true,
    };
  }
});

// Register prompts (if MCP SDK supports prompts in the future)
registerWorkflowCsvPrompt(server);
registerWorkflowWavPrompt(server);

// Start server
async function startServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  const API_URL = process.env.TOORPIA_API_URL ?? "http://localhost:3000";
  const ENABLE_WAV = process.env.ENABLE_WAV !== "false";
  
  console.error("=".repeat(60));
  console.error("toorpia-mcp server started (stdio)");
  console.error(`API_URL: ${API_URL}`);
  console.error(`ENABLE_WAV: ${ENABLE_WAV}`);
  console.error(`Tools registered: ${allToolDefinitions.length}`);
  console.error("- Common tools: locate_file, detect_file_type, whoami, list_map, etc.");
  console.error("- CSV tools: fit_transform, addplot");
  console.error("- WAV tools: fit_transform_waveform, addplot_waveform");
  console.error("=".repeat(60));
}

// Handle startup
startServer().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
