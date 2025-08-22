# toorPIA MCP Server

MCP (Model Context Protocol) server implementation providing comprehensive tools for toorPIA API integration.

## Architecture

This server implements a modular architecture with separated concerns:

```
src/
├─ server.ts                 # Main entry point (MCP server startup)
├─ tools/
│  ├─ common.ts             # Common tools (locate_file, detect_file_type, etc.)
│  ├─ csv.ts                # CSV workflow (fit_transform, addplot, csv.*)
│  └─ wav.ts                # WAV workflow (ENABLE_WAV controlled)
├─ prompts/
│  ├─ workflow_csv.ts       # CSV workflow guidance
│  └─ workflow_wav.ts       # WAV workflow guidance
├─ client/
│  └─ toorpia.ts            # toorPIA API client
└─ types.ts                 # Shared type definitions
```

## Installation & Build

```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Production build
npm run build

# Start production server
npm start
```

## Environment Configuration

Create `.env` from `.env.example`:

```bash
# toorPIA API Configuration
TOORPIA_API_KEY=your_api_key_here
TOORPIA_API_URL=http://localhost:3000

# Feature Control
ENABLE_WAV=true
```

## Available Tools

### Core Tools (10 legacy tools - full compatibility maintained)
- `fit_transform`: Create base map from CSV/DataFrame data
- `addplot`: Add data to existing maps
- `fit_transform_waveform`: Create base map from WAV files
- `addplot_waveform`: Add WAV files to maps
- `list_map`: List all maps
- `list_addplots`: List addplots for a map
- `get_addplot`: Get addplot details
- `get_addplot_features`: Get feature data
- `export_map`: Export map data
- `import_map`: Import map data
- `whoami`: Authentication verification

### New Common Tools
- `locate_file`: File existence check and absolute path resolution
- `detect_file_type`: File format detection (CSV/WAV/unknown)

### CSV Workflow Tools (5 new interactive tools)
- `csv.preview`: CSV structure analysis with automatic type inference
- `csv.apply_schema_patch`: Interactive schema adjustment
- `csv.get_schema`: Schema state retrieval
- `csv.generate_runner`: toorPIA-compliant Python script generation
- `csv.run_runner`: Synchronous Python script execution

## Type System

### Column Types
```typescript
type ColType = "integer" | "number" | "boolean" | "datetime" | "string";

interface ColSpec {
  name: string;
  type: ColType;
  weight: number;  // Default weights: num/int=1.0, datetime=0.8, boolean=0.6, string=0.5
  use: boolean;    // Default: true
  description?: string;
}
```

### Error Handling
All tools return unified error format:
```typescript
{
  ok: false,
  code: "ERROR_CODE",
  reason: "Detailed error message"
}
```

**CSV Workflow Error Codes:**
- `NOT_FOUND`: File or data not found
- `SCHEMA_NOT_INITIALIZED`: Schema not initialized (csv.preview required)
- `SCHEMA_NOT_READY`: Schema preparation incomplete
- `UNKNOWN_COLUMN`: Specified column does not exist
- `RUNTIME_ERROR`: Execution error
- `PYTHON_NOT_FOUND`: python3 command not available

## Development Guidelines

### Adding New Tools
1. Implement in appropriate `src/tools/[category].ts`
2. Add to tool definitions array
3. Update handlers map
4. Register in `src/server.ts`

### Error Handling Pattern
```typescript
async function toolHandler(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    // Tool implementation
    const result = { ok: true, data: "success" };
    logTool("tool_name", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: "ERROR_CODE", reason: error.message };
    logTool("tool_name", "ERROR_CODE", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}
```

### Logging Standard
All tools must use unified logging:
```typescript
logTool(toolName: string, result: "OK" | string, durationMs: number);
// Output: [TOOL] tool_name: OK (123ms)
// Output: [TOOL] tool_name: ERROR:ERROR_CODE (45ms)
```

## CSV Workflow Implementation Details

### Type Inference Logic
- **Boolean**: `/^(true|false|1|0|yes|no)$/i` pattern matching
- **DateTime**: `Date.parse()` success + datetime pattern validation
- **Integer/Number**: Numeric validation + integer checking
- **String**: Default fallback

### Schema Storage
- Global `Map<string, Schema>` keyed by absolute file paths
- Thread-safe in-memory storage during server session
- Schema persists across tool calls within same session

### Python Script Generation
Template-based generation with:
- `CSV_PATH`: File path interpolation
- `DROP_COLUMNS`: Auto-generated from `use:false` or `weight:0` columns
- toorPIA client integration: `toorPIA().fit_transform(df)`

## Testing

### Test Data
- `testdata/sensor_log.csv`: Sample sensor data (20 rows, 7 columns)
- Mixed data types: timestamp, numeric, boolean, string values
- Ready for complete workflow testing

### Workflow Testing
```bash
# 1. File verification
locate_file -> get absolute path
detect_file_type -> confirm CSV format

# 2. Schema initialization
csv.preview -> auto type inference, sample data

# 3. Schema adjustment (optional)
csv.apply_schema_patch -> modify column settings

# 4. Script generation
csv.generate_runner -> create toorPIA Python script

# 5. Execution
csv.run_runner -> execute and get results
```

## API Compatibility

**100% backward compatibility maintained** for all existing tools. New CSV workflow tools are additive and do not affect legacy functionality.

## Requirements

### Runtime Dependencies
- Node.js (ES modules support)
- TypeScript compilation target
- MCP SDK compatible environment

### Python Environment (for csv.run_runner)
- `python3` command available
- `toorpia` package installed: `pip install toorpia`
- `TOORPIA_API_KEY` environment variable configured

## Deployment

### Production Build
```bash
npm run build
# Creates dist/ directory with compiled JavaScript

npm start
# Runs dist/server.js
```

### MCP Client Integration
```json
{
  "mcpServers": {
    "toorpia-mcp": {
      "command": "node",
      "args": ["./dist/server.js"],
      "cwd": "/path/to/mcp",
      "env": {
        "TOORPIA_API_KEY": "your_key",
        "TOORPIA_API_URL": "http://localhost:3000",
        "ENABLE_WAV": "true"
      }
    }
  }
}
```
