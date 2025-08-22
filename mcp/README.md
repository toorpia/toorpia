# toorPIA MCP Server

MCP (Model Context Protocol) server implementation providing comprehensive tools for toorPIA API integration.

## Architecture

Modular server implementation with separated concerns, evolved from monolithic single-file to structured architecture:

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

## Quick Start

### Development Mode
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# toorPIA API Configuration
TOORPIA_API_KEY=your_api_key_here
TOORPIA_API_URL=http://localhost:3000

# Feature Control
ENABLE_WAV=true
```

### Important: TOORPIA_API_KEY Setup

**Required for CSV workflow Python script execution:**

1. **Set as environment variable** (recommended):
   ```bash
   export TOORPIA_API_KEY="your_actual_api_key_here"
   ```

2. **Specify at MCP server startup**:
   ```json
   {
     "env": {
       "TOORPIA_API_KEY": "your_actual_api_key_here"
     }
   }
   ```

3. **Python environment prerequisites**:
   - `python3` command available
   - `pip install toorpia` package installed
   - `TOORPIA_API_KEY` environment variable configured

### ENABLE_WAV Control

- `ENABLE_WAV=true` (default): WAV functionality enabled
- `ENABLE_WAV=false`: WAV functionality disabled (NOT_IMPLEMENTED response)

## Available Tools

### New Common Tools

#### locate_file
File existence verification and absolute path resolution

```json
// Input
{
  "baseDir": "/path/to/base", // optional
  "path": "relative/file.csv"
}

// Output (Success)
{
  "ok": true,
  "absPath": "/path/to/base/relative/file.csv",
  "exists": true
}

// Output (Error)
{
  "ok": false,
  "code": "LOCATE_ERROR",
  "reason": "Error details"
}
```

#### detect_file_type
File format detection (CSV/WAV/unknown)

```json
// Input
{
  "path": "/path/to/file.wav"
}

// Output (WAV)
{
  "ok": true,
  "kind": "wav",
  "reason": "Detected WAV by RIFF header"
}

// Output (CSV)
{
  "ok": true,
  "kind": "csv", 
  "reason": "Detected CSV by extension"
}

// Output (Unknown)
{
  "ok": true,
  "kind": "unknown",
  "reason": "Unknown file type with extension: .txt"
}
```

### Legacy Tools (Full API Compatibility Maintained)

The following 10 tools maintain complete compatibility:

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

## Unified Error Response

All tools use unified error format:

```json
{
  "ok": false,
  "code": "ERROR_CODE",
  "reason": "Detailed error description"
}
```

## Logging Output

Each tool call generates log output:
```
[TOOL] tool_name: OK (123ms)
[TOOL] tool_name: ERROR:AUTH_FAILED (45ms)
```

## MCP Client Configuration Examples

### Claude Desktop
`mcp_settings.json`:
```json
{
  "mcpServers": {
    "toorpia-mcp": {
      "command": "node",
      "args": ["./dist/server.js"],
      "cwd": "/path/to/toorpia-mcp",
      "env": {
        "TOORPIA_API_KEY": "your_key_here",
        "TOORPIA_API_URL": "http://localhost:3000",
        "ENABLE_WAV": "true"
      }
    }
  }
}
```

### MCP Inspector
```bash
node ./dist/server.js
```

## CSV Workflow

Complete interactive CSV data processing pipeline:

### csv.preview
CSV file automatic type inference and schema initialization

```json
// Input
{
  "path": "/absolute/path/to/file.csv",
  "nRows": 5  // optional, default: 5
}

// Output
{
  "ok": true,
  "filePath": "/absolute/path/to/file.csv",
  "rowCount": 20,
  "columns": [
    {
      "name": "timestamp",
      "type": "datetime",
      "weight": 0.8,
      "use": true
    },
    {
      "name": "temperature", 
      "type": "number",
      "weight": 1.0,
      "use": true
    }
  ],
  "sampleData": [
    ["2024-01-01T10:00:00", 23.5],
    ["2024-01-01T10:05:00", 23.7]
  ]
}
```

### csv.apply_schema_patch
Column schema adjustment (type, weight, usage flags)

```json
// Input
{
  "path": "/absolute/path/to/file.csv",
  "patches": [
    {
      "columnName": "sensor_id",
      "updates": {
        "type": "string",
        "weight": 0.0,
        "use": false,
        "description": "Exclude sensor ID from analysis"
      }
    }
  ]
}

// Output  
{
  "ok": true,
  "updatedColumns": ["sensor_id"]
}
```

### csv.get_schema
Current schema state verification

```json
// Input
{
  "path": "/absolute/path/to/file.csv"
}

// Output
{
  "ok": true,
  "schema": {
    "filePath": "/absolute/path/to/file.csv",
    "columns": [...],
    "rowCount": 20,
    "sampleData": [...],
    "description": "CSV file with 20 rows and 7 columns"
  }
}
```

### csv.generate_runner
toorPIA-compliant Python script generation

```json
// Input
{
  "path": "/absolute/path/to/file.csv",
  "outputPath": "/path/to/script.py"  // optional
}

// Output
{
  "ok": true,
  "script": "#!/usr/bin/env python3\n# Auto-generated script...",
  "scriptPath": "/path/to/script.py"
}
```

### csv.run_runner
Synchronous Python script execution

```json
// Input
{
  "scriptContent": "import pandas as pd\nfrom toorpia import toorPIA\n..."
}

// Output (Success)
{
  "ok": true,
  "stdout": "Loading CSV data...\nAnalysis complete!",
  "stderr": "",
  "exitCode": 0
}

// Output (Error)
{
  "ok": false,
  "code": "RUNTIME_ERROR",
  "reason": "Python script failed with exit code 1: ModuleNotFoundError: No module named 'toorpia'"
}
```

### Complete Workflow Example

Using testdata/sensor_log.csv:

```bash
# 1. File verification
locate_file -> get absolute path
detect_file_type -> confirm CSV format

# 2. Schema initialization  
csv.preview -> automatic type inference, display sample data

# 3. Schema adjustment (optional)
csv.apply_schema_patch -> exclude unnecessary columns, adjust weights

# 4. Python script generation
csv.generate_runner -> auto-configure DROP_COLUMNS, toorPIA invocation

# 5. Execution
csv.run_runner -> execute analysis, retrieve results
```

### Error Codes

CSV workflow-specific errors:
- `NOT_FOUND`: File or data not found
- `SCHEMA_NOT_INITIALIZED`: Schema not initialized (csv.preview required)
- `SCHEMA_NOT_READY`: Schema preparation incomplete
- `UNKNOWN_COLUMN`: Specified column does not exist
- `RUNTIME_ERROR`: Runtime error
- `PYTHON_NOT_FOUND`: python3 command not found

## Implementation Status

### ✅ Completed
- **File Split Refactoring**: From monolithic to structured architecture
- **API Compatibility**: Complete compatibility for existing 10 tools
- **New Tools**: locate_file, detect_file_type
- **CSV Workflow**: Complete pipeline: preview→adjustment→generation→execution
  - csv.preview: Automatic type inference and schema initialization
  - csv.apply_schema_patch: Interactive schema adjustment
  - csv.get_schema: Schema state verification
  - csv.generate_runner: toorPIA-compliant script generation
  - csv.run_runner: Python synchronous execution
- **Unified Error Response**: {ok, code, reason} format
- **Logging Functionality**: [TOOL] name: status (duration)ms
- **ENABLE_WAV Control**: Environment variable feature control
- **Prompt Registration**: Complete workflow guidance

### 🚧 Future Implementation (Upcoming PRs)
- Detailed WAV functionality implementation
- Actual prompt registration (when MCP SDK supports it)
- Additional data processing pipelines

## Developer Guide

### Adding Tools
1. Implement in `src/tools/[category].ts`
2. Import and register in `src/server.ts`

### Error Handling
- Use unified `{ok, code, reason}` format
- Call log function `logTool(name, result, duration)`

### Environment Variables
- Implement feature control via environment variables
- Add new variables to `.env.example`
