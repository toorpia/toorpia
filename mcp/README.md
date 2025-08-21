# toorPIA MCP Server

This is a Model Context Protocol (MCP) server that provides access to toorPIA API endpoints as MCP tools. It enables seamless integration of toorPIA's data analysis capabilities into applications supporting MCP, such as Claude Desktop.

## Features Overview

The toorPIA MCP server exposes toorPIA API functionality as MCP tools, providing the following operations:

### Data Analysis Functions
- **fit_transform**: Create base map from DataFrame data
- **addplot**: Add data to existing map (including anomaly detection)
- **fit_transform_waveform**: Create base map from WAV/CSV files
- **addplot_waveform**: Add WAV/CSV files to existing map

### Map Management Functions
- **list_map**: List available maps
- **export_map**: Export map (save locally)
- **import_map**: Import map (load from local)

### Additional Plot Functions
- **list_addplots**: List additional plots for a map
- **get_addplot**: Get details of specific additional plot
- **get_addplot_features**: Feature analysis of additional plots

### Authentication & Health Functions
- **whoami**: Check authentication status

## Setup

### 1. Install Dependencies

```bash
cd mcp
npm install
```

### 2. Build TypeScript

```bash
npm run build
```

### 3. Environment Variables

Set the following environment variables:

```bash
export TOORPIA_API_KEY="your-api-key-here"
export TOORPIA_API_URL="http://localhost:3000"  # Optional (default: http://localhost:3000)
```

### 4. Claude Desktop Integration

Add the following to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "toorpia": {
      "command": "node",
      "args": ["./dist/index.js"],
      "cwd": "/path/to/your/toorpia/mcp",
      "env": {
        "TOORPIA_API_KEY": "your-actual-api-key",
        "TOORPIA_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

**Important**: 
- Replace `/path/to/your/toorpia/mcp` with the actual path
- Replace `your-actual-api-key` with your actual API key

## Available Tools

### Data Processing Tools

#### fit_transform
Creates a base map from DataFrame data (pandas orient='split' format).

**Parameters:**
- `data`: DataFrame (orient='split' format)
- `label`, `tag`, `description`: Metadata (optional)
- `weight_option_str`, `type_option_str`: Column weight and type settings (optional)
- `identna_resolution`, `identna_effective_radius`: identna parameters (optional)

#### addplot
Adds DataFrame data to an existing map and performs anomaly detection.

**Parameters:**
- `data`: DataFrame (orient='split' format)
- `mapNo`: Target map number (optional, uses last fit_transform map if omitted)
- `detabn_*`: Anomaly detection parameters (optional)
- `mode`: 'xy' (coordinates only) or 'full' (complete information, default)

#### fit_transform_waveform
Creates a base map from WAV or CSV files.

**Parameters:**
- `files`: Array of file paths
- `mkfftseg_*`: FFT segmentation parameters (optional)
- `identna_*`: identna parameters (optional)
- `label`, `tag`, `description`: Metadata (optional)

#### addplot_waveform
Adds WAV or CSV files to an existing map and performs anomaly detection.

**Parameters:**
- `files`: Array of file paths
- `mapNo`: Target map number (optional)
- `mkfftseg_*`: FFT segmentation parameters (optional)
- `detabn_*`: Anomaly detection parameters (optional)

### Map Management Tools

#### list_map
Retrieves a list of available maps.

#### export_map
Exports a specified map to a local directory.

**Parameters:**
- `mapNo`: Map number to export
- `exportDir`: Export destination directory path

#### import_map
Imports a map from a local directory.

**Parameters:**
- `inputDir`: Import source directory path

### Additional Plot Management Tools

#### list_addplots
Retrieves a list of additional plots for a specified map.

**Parameters:**
- `mapNo`: Target map number

#### get_addplot
Retrieves detailed information about a specific additional plot.

**Parameters:**
- `mapNo`: Target map number
- `addplotNo`: Additional plot number

#### get_addplot_features
Retrieves feature analysis results for an additional plot.

**Parameters:**
- `mapNo`: Target map number
- `addplotNo`: Additional plot number
- `use_tscore`: Whether to use T-score (default: false, uses Z-score)

## Development & Debugging

### Development Mode
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Production Run
```bash
npm start
```

## Correspondence with client.py

This MCP server provides nearly complete coverage of the toorPIA Python client.py functionality:

| Python client.py | MCP Tool | Description |
|------------------|----------|-------------|
| `fit_transform()` | `fit_transform` | Create base map from DataFrame |
| `addplot()` | `addplot` | DataFrame additional plot |
| `fit_transform_waveform()` | `fit_transform_waveform` | Create base map from waveform files |
| `addplot_waveform()` | `addplot_waveform` | Waveform file additional plot |
| `list_map()` | `list_map` | List maps |
| `export_map()` / `download_map()` | `export_map` | Export map |
| `import_map()` / `upload_map()` | `import_map` | Import map |
| `list_addplots()` | `list_addplots` | List additional plots |
| `get_addplot()` | `get_addplot` | Get additional plot details |
| `get_addplot_features()` | `get_addplot_features` | Feature analysis |
| `authenticate()` | Auto-executed | Authentication (automatically executed on each tool run) |

## Important Notes

1. **File Paths**: When processing waveform files, specify file paths accessible from the MCP server
2. **Authentication**: Authentication is performed automatically on each tool execution (no explicit authentication required)
3. **Session Management**: Session keys are managed automatically
4. **Error Handling**: API errors are properly reported as MCP tool errors

## Troubleshooting

### Authentication Errors
- Verify that the `TOORPIA_API_KEY` environment variable is set correctly
- Confirm that the API key is valid
- Check authentication status with the `whoami` tool

### Connection Errors
- Verify that `TOORPIA_API_URL` is correct
- Confirm that the toorPIA API server is running
- Check network connectivity

### File Access Errors
- Verify that the specified file path exists
- Confirm that the MCP server has read permissions for the file

## License

This MCP server is provided as part of the toorPIA API client library.
