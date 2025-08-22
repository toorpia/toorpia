import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const CSV_WORKFLOW_PROMPT = `# CSV Data Processing Workflow Complete Guide

The toorPIA MCP Server's CSV workflow provides an interactive data analysis pipeline.

## CSV Workflow: Preview → Schema Adjustment → Finalize → Script Generation → Execution

### Step 1: File Verification and Initialization
\`\`\`bash
# File location verification
locate_file: File existence check and absolute path retrieval
- path: File path
- baseDir (optional): Base directory

detect_file_type: File format detection
- path: File path
- Return value: Continue CSV workflow only if kind="csv"

# CSV preview and schema initialization
csv.preview: CSV structure verification and automatic type inference
- path: Absolute file path (obtained from locate_file)
- nRows: Number of sample rows (default: 5)

Example return value:
{
  "ok": true,
  "filePath": "/path/to/file.csv",
  "rowCount": 100,
  "columns": [
    {"name": "timestamp", "type": "datetime", "weight": 0.8, "use": true},
    {"name": "temperature", "type": "number", "weight": 1.0, "use": true},
    {"name": "sensor_id", "type": "string", "weight": 0.5, "use": true}
  ],
  "sampleData": [["2024-01-01T10:00:00", 23.5, "TEMP_001"], ...]
}
\`\`\`

### Step 2: Schema Adjustment (Optional)
\`\`\`bash
# Column configuration changes
csv.apply_schema_patch: Column attribute modification
- path: Absolute file path
- patches: Array of modification details
  - columnName: Column name
  - updates: 
    - type: "integer"|"number"|"boolean"|"datetime"|"string"
    - weight: Weight value (0.0-1.0)
    - use: Usage flag (true/false)
    - description: Description (optional)

# Current schema verification
csv.get_schema: Schema state retrieval
- path: Absolute file path
\`\`\`

### Step 3: Script Generation
\`\`\`bash
csv.generate_runner: toorPIA-compliant Python script generation
- path: Absolute file path
- outputPath: Output path (optional)

# Auto-generated content:
# - CSV_PATH: File path
# - DROP_COLUMNS: Columns with use:false or weight:0
# - toorPIA().fit_transform(df) invocation
\`\`\`

### Step 4: Script Execution
\`\`\`bash
csv.run_runner: Synchronous Python script execution
- scriptContent: Python code to execute

# Prerequisites:
# - python3 command available
# - toorpia package installed
# - TOORPIA_API_KEY environment variable set

Return value:
{
  "ok": true,
  "stdout": "Execution results...",
  "stderr": "Error output...",
  "exitCode": 0
}
\`\`\`

## Type Inference System

The CSV workflow performs the following automatic type inference:

### Supported Types
- **integer**: Integer values
- **number**: Floating-point numbers
- **boolean**: true/false, 1/0, yes/no patterns
- **datetime**: Date.parse() success with datetime patterns
- **string**: Other string data

### Default Weights
- integer/number: 1.0
- datetime: 0.8  
- boolean: 0.6
- string: 0.5

## Error Handling

Unified error response format \`{ ok: false, code, reason }\`:

- **NOT_FOUND**: File or data not found
- **SCHEMA_NOT_INITIALIZED**: Schema not initialized
- **SCHEMA_NOT_READY**: Schema preparation incomplete
- **UNKNOWN_COLUMN**: Specified column does not exist
- **RUNTIME_ERROR**: Runtime error
- **PYTHON_NOT_FOUND**: Python environment not found

## Legacy Tools (Backward Compatibility)

Traditional fit_transform and addplot tools remain available:
- fit_transform: Direct map creation from pandas orient="split" data
- addplot: Data addition to existing maps

## WAV Workflow

WAV file processing is currently under development.
When detect_file_type detects kind="wav", please check the following:

- WAV file processing functionality: refer to workflow_wav prompt
- Currently only basic detection functionality is implemented
- Full functionality is controlled by ENABLE_WAV environment variable

## Usage Example

Sample workflow using testdata/sensor_log.csv:

1. Verify file path with \`locate_file\`
2. Confirm CSV format with \`detect_file_type\`  
3. Initialize schema with \`csv.preview\`
4. Adjust with \`csv.apply_schema_patch\` if needed
5. Generate Python script with \`csv.generate_runner\`
6. Execute analysis with \`csv.run_runner\`

All tools are recorded in unified log format \`[TOOL] name: status (duration)ms\`.
`;

export function registerWorkflowCsvPrompt(server: Server): void {
  // プロンプト登録の実装
  // Note: 実際のMCP SDK のプロンプト機能が利用可能な場合に実装
  console.error("[PROMPT] workflow_csv registered");
}

export const csvWorkflowPrompt = CSV_WORKFLOW_PROMPT;
