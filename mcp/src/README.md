# Source Code Documentation

Developer documentation for toorPIA MCP Server source code.

## Quick Start

```bash
npm install
npm run dev    # Development mode
npm run build  # Production build
```

## Source Structure

```
src/
├─ server.ts          # MCP server entry point
├─ types.ts           # Shared type definitions  
├─ client/
│  └─ toorpia.ts      # API client implementation
├─ tools/             # Tool implementations
│  ├─ common.ts       # Common utilities
│  ├─ csv.ts          # CSV workflow tools
│  └─ wav.ts          # WAV workflow tools
└─ prompts/           # Workflow guidance templates
   ├─ workflow_csv.ts
   └─ workflow_wav.ts
```

## Development Patterns

### Tool Implementation
```typescript
// 1. Define tool handler
async function toolHandler(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    // Implementation
    logTool("tool_name", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    logTool("tool_name", "ERROR_CODE", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify({ok: false, code, reason}) }] };
  }
}

// 2. Add to tool definitions
const toolDefinitions = [{
  name: "tool_name",
  description: "Tool description",
  inputSchema: z.object({...}),
  handler: toolHandler
}];

// 3. Register in handlers map
toolHandlers.set("tool_name", toolHandler);
```

### Error Response Format
```typescript
interface ErrorResponse {
  ok: false;
  code: string;
  reason: string;
}
```

### Logging Standard
```typescript
logTool(name: string, result: "OK" | string, durationMs: number);
```

For complete API documentation and usage examples, see the main [README](../README.md).
