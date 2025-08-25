import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { parse } from "csv-parse/sync";
import { readFileSync, existsSync } from "fs";
import { spawn, spawnSync } from "child_process";
import { join, dirname } from "path";
import { toorpiaClient } from "../client/toorpia.js";
import { SplitDF } from "./common.js";
import {
  ColType, 
  ColSpec, 
  Schema, 
  ERROR_CODES,
  ErrorResponse,
  PreviewResponse,
  SchemaResponse,
  PatchResponse,
  RunnerResponse,
  ExecutionResponse
} from "../types.js";

// Global schema storage - keyed by absolute path
const schemaStore = new Map<string, Schema>();

// Logging function
function logTool(name: string, result: "OK" | string, durationMs: number): void {
  const status = result === "OK" ? "OK" : `ERROR:${result}`;
  console.error(`[TOOL] ${name}: ${status} (${durationMs}ms)`);
}

// Type inference helper functions
function inferColumnType(values: string[]): ColType {
  // Filter out empty/null values
  const nonEmptyValues = values.filter(v => v !== null && v !== undefined && v !== "");
  if (nonEmptyValues.length === 0) return "none";
  
  // Number patterns
  const numericValues = nonEmptyValues.filter(v => !isNaN(Number(v)));
  if (numericValues.length === nonEmptyValues.length) {
    // Check if all are integers
    const allIntegers = numericValues.every(v => Number.isInteger(Number(v)));
    return allIntegers ? "int" : "float";
  }
  
  // DateTime pattern: try Date.parse
  const dateValues = nonEmptyValues.filter(v => !isNaN(Date.parse(v.toString())));
  if (dateValues.length === nonEmptyValues.length && nonEmptyValues.length > 0) {
    // Additional check: make sure it's not just a number that Date.parse accepts
    const hasDateLikePattern = nonEmptyValues.some(v => 
      /[-\/:\s]/.test(v.toString()) || v.toString().length > 10
    );
    if (hasDateLikePattern) {
      return "date";
    }
  }
  
  // Enum pattern: limited unique values (categorical data)
  const uniqueValues = [...new Set(nonEmptyValues)];
  if (uniqueValues.length <= 10 && uniqueValues.length < nonEmptyValues.length * 0.5) {
    return "enum";
  }
  
  return "none";
}

function getDefaultWeight(type: ColType, use: boolean): number {
  // float, int, enum かつ use: true の場合のみ重み1.0
  if (use && (type === "float" || type === "int" || type === "enum")) {
    return 1.0;
  }
  return 0.0;
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

// CSV Workflow Tools Implementation

// 1. CSV Preview Tool
async function csvPreview(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { path, nRows = 5 } = args;
    
    if (!existsSync(path)) {
      const result = { ok: false, code: ERROR_CODES.NOT_FOUND, reason: `File not found: ${path}` };
      logTool("csv.preview", ERROR_CODES.NOT_FOUND, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const fileContent = readFileSync(path, 'utf-8');
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
      trim: true
    });

    if (records.length === 0) {
      const result = { ok: false, code: ERROR_CODES.NOT_FOUND, reason: "No data found in CSV file" };
      logTool("csv.preview", ERROR_CODES.NOT_FOUND, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const columnNames = Object.keys(records[0]);
    const sampleData = records.slice(0, nRows);
    
    // Infer column types from all data (not just sample)
    const columns: ColSpec[] = columnNames.map(name => {
      const columnValues = records.map(record => record[name]).filter(v => v !== null && v !== undefined);
      const inferredType = inferColumnType(columnValues);
      const defaultUse = true;
      
      return {
        name,
        type: inferredType,
        weight: getDefaultWeight(inferredType, defaultUse),
        use: defaultUse
      };
    });

    const schema: Schema = {
      filePath: path,
      columns,
      rowCount: records.length,
      sampleData: sampleData.map(record => columnNames.map(name => record[name])),
      description: `CSV file with ${records.length} rows and ${columnNames.length} columns`
    };

    // Store schema in global storage
    schemaStore.set(path, schema);

    const result: PreviewResponse = {
      ok: true,
      filePath: path,
      rowCount: records.length,
      columns,
      sampleData: schema.sampleData
    };

    logTool("csv.preview", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: error.message };
    logTool("csv.preview", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// 2. Apply Schema Patch Tool  
async function csvApplySchemaPatch(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { path, patches } = args;
    
    const schema = schemaStore.get(path);
    if (!schema) {
      const result = { ok: false, code: ERROR_CODES.SCHEMA_NOT_INITIALIZED, reason: `Schema not found for path: ${path}` };
      logTool("csv.apply_schema_patch", ERROR_CODES.SCHEMA_NOT_INITIALIZED, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const updatedColumns: string[] = [];
    
    for (const patch of patches) {
      const { columnName, updates } = patch;
      const columnIndex = schema.columns.findIndex(col => col.name === columnName);
      
      if (columnIndex === -1) {
        const result = { ok: false, code: ERROR_CODES.UNKNOWN_COLUMN, reason: `Column not found: ${columnName}` };
        logTool("csv.apply_schema_patch", ERROR_CODES.UNKNOWN_COLUMN, Date.now() - startTime);
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }

      // Apply updates
      if (updates.type !== undefined) schema.columns[columnIndex].type = updates.type;
      if (updates.weight !== undefined) schema.columns[columnIndex].weight = updates.weight;
      if (updates.use !== undefined) schema.columns[columnIndex].use = updates.use;
      if (updates.description !== undefined) schema.columns[columnIndex].description = updates.description;
      
      updatedColumns.push(columnName);
    }

    // Update schema in storage
    schemaStore.set(path, schema);

    const result: PatchResponse = {
      ok: true,
      updatedColumns
    };

    logTool("csv.apply_schema_patch", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: error.message };
    logTool("csv.apply_schema_patch", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// 3. Get Schema Tool
async function csvGetSchema(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { path } = args;
    
    const schema = schemaStore.get(path);
    if (!schema) {
      const result = { ok: false, code: ERROR_CODES.SCHEMA_NOT_INITIALIZED, reason: `Schema not found for path: ${path}` };
      logTool("csv.get_schema", ERROR_CODES.SCHEMA_NOT_INITIALIZED, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const result: SchemaResponse = {
      ok: true,
      schema
    };

    logTool("csv.get_schema", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: error.message };
    logTool("csv.get_schema", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// 4. Generate Runner Tool
async function csvGenerateRunner(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { path, outputPath } = args;
    
    const schema = schemaStore.get(path);
    if (!schema) {
      const result = { ok: false, code: ERROR_CODES.SCHEMA_NOT_INITIALIZED, reason: `Schema not found for path: ${path}` };
      logTool("csv.generate_runner", ERROR_CODES.SCHEMA_NOT_INITIALIZED, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    // Generate DROP_COLUMNS list
    const dropColumns = schema.columns
      .filter(col => !col.use || col.weight === 0)
      .map(col => col.name);

    // Python script template
    const script = `#!/usr/bin/env python3
"""
Auto-generated CSV analysis script using toorPIA
Generated from schema: ${schema.filePath}
"""

import pandas as pd
from toorpia import toorPIA

# Configuration
CSV_PATH = "${path}"
DROP_COLUMNS = ${JSON.stringify(dropColumns)}

def main():
    # Load CSV data
    print(f"Loading CSV data from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Original shape: {df.shape}")
    
    # Drop unused columns
    if DROP_COLUMNS:
        print(f"Dropping columns: {DROP_COLUMNS}")
        df = df.drop(columns=DROP_COLUMNS)
        print(f"Shape after dropping columns: {df.shape}")
    
    # Initialize toorPIA client
    client = toorPIA()
    
    # Perform fit_transform
    print("Performing fit_transform...")
    result = client.fit_transform(df)
    
    print("Analysis complete!")
    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict result'}")
    
    return result

if __name__ == "__main__":
    result = main()
    print("Final result:", result)
`;

    const result: RunnerResponse = {
      ok: true,
      script,
      scriptPath: outputPath
    };

    logTool("csv.generate_runner", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: error.message };
    logTool("csv.generate_runner", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// 5. Run Runner Tool
async function csvRunRunner(args: any): Promise<CallToolResult> {
  const startTime = Date.now();
  try {
    const { scriptContent } = args;

    // Check if python3 is available
    try {
      const pythonCheck = spawnSync('python3', ['--version'], { encoding: 'utf8' });
      if (pythonCheck.error) {
        const result = { ok: false, code: ERROR_CODES.PYTHON_NOT_FOUND, reason: "python3 command not found" };
        logTool("csv.run_runner", ERROR_CODES.PYTHON_NOT_FOUND, Date.now() - startTime);
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }
    } catch (error) {
      const result = { ok: false, code: ERROR_CODES.PYTHON_NOT_FOUND, reason: "Failed to check python3 availability" };
      logTool("csv.run_runner", ERROR_CODES.PYTHON_NOT_FOUND, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    // Execute Python script
    const pythonProcess = spawnSync('python3', ['-c', scriptContent], {
      encoding: 'utf8',
      timeout: 60000 // 60 second timeout
    });

    if (pythonProcess.error) {
      const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: pythonProcess.error.message };
      logTool("csv.run_runner", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    if (pythonProcess.status !== 0) {
      const result = { 
        ok: false, 
        code: ERROR_CODES.RUNTIME_ERROR, 
        reason: `Python script failed with exit code ${pythonProcess.status}: ${pythonProcess.stderr}` 
      };
      logTool("csv.run_runner", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }

    const result: ExecutionResponse = {
      ok: true,
      stdout: pythonProcess.stdout || "",
      stderr: pythonProcess.stderr || "",
      exitCode: pythonProcess.status || 0
    };

    logTool("csv.run_runner", "OK", Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error: any) {
    const result = { ok: false, code: ERROR_CODES.RUNTIME_ERROR, reason: error.message };
    logTool("csv.run_runner", ERROR_CODES.RUNTIME_ERROR, Date.now() - startTime);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
}

// CSV tool definitions
const csvToolDefinitions = [
  // Legacy tools
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
      identna_effective_radius: z.number().optional()
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
      mode: z.enum(["xy", "full"]).optional()
    }),
    handler: addplot
  },
  // New CSV Workflow tools
  {
    name: "csv.preview",
    description: "Preview CSV file structure with automatic type inference and schema initialization. Default nRows=5.",
    inputSchema: z.object({
      path: z.string().describe("Absolute path to CSV file"),
      nRows: z.number().optional().describe("Number of sample rows to include (default: 5)")
    }),
    handler: csvPreview
  },
  {
    name: "csv.apply_schema_patch",
    description: "Apply patches to modify column schema (type, weight, use flag). Requires existing schema.",
    inputSchema: z.object({
      path: z.string().describe("Absolute path to CSV file"),
      patches: z.array(z.object({
        columnName: z.string(),
        updates: z.object({
          type: z.enum(["float", "int", "enum", "date", "none"]).optional(),
          weight: z.number().optional(),
          use: z.boolean().optional(),
          description: z.string().optional()
        })
      })).describe("Array of column patches to apply")
    }),
    handler: csvApplySchemaPatch
  },
  {
    name: "csv.get_schema",
    description: "Retrieve current schema for a CSV file. Schema must be initialized via csv.preview first.",
    inputSchema: z.object({
      path: z.string().describe("Absolute path to CSV file")
    }),
    handler: csvGetSchema
  },
  {
    name: "csv.generate_runner",
    description: "Generate Python script using toorPIA template. DROP_COLUMNS includes use:false or weight:0 columns.",
    inputSchema: z.object({
      path: z.string().describe("Absolute path to CSV file"),
      outputPath: z.string().optional().describe("Optional output path for generated script")
    }),
    handler: csvGenerateRunner
  },
  {
    name: "csv.run_runner",
    description: "Execute Python script synchronously. Requires python3 and toorpia package. Returns stdout/stderr.",
    inputSchema: z.object({
      scriptContent: z.string().describe("Python script content to execute")
    }),
    handler: csvRunRunner
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
