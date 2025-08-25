// Common type definitions for toorPIA MCP server

// CSV Workflow specific types
export type ColType = "float" | "int" | "enum" | "date" | "none";

export interface ColSpec {
  name: string;
  type: ColType;
  weight: number;  // float/int/enum + use=true: 1.0, others: 0.0
  use: boolean;    // Default: true
  description?: string;
}

export interface Schema {
  filePath: string;      // Absolute path from locate_file
  columns: ColSpec[];
  rowCount: number;
  sampleData: any[][];   // Sample rows (nRows=5)
  description?: string;
}

// Error codes for CSV workflow
export const ERROR_CODES = {
  NOT_FOUND: "NOT_FOUND",
  SCHEMA_NOT_INITIALIZED: "SCHEMA_NOT_INITIALIZED",
  SCHEMA_NOT_READY: "SCHEMA_NOT_READY", 
  UNKNOWN_COLUMN: "UNKNOWN_COLUMN",
  RUNTIME_ERROR: "RUNTIME_ERROR",
  PYTHON_NOT_FOUND: "PYTHON_NOT_FOUND"
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

// Standard error response format
export interface ErrorResponse {
  ok: false;
  code: string;
  reason: string;
}

// Success response formats  
export interface SuccessResponse<T = any> {
  ok: true;
  data?: T;
}

// File operation responses
export interface FileLocationResponse {
  ok: boolean;
  absPath?: string;
  exists?: boolean;
  code?: string;
  reason?: string;
}

export interface FileTypeResponse {
  ok: boolean;
  kind?: "csv" | "wav" | "unknown";
  reason?: string;
  code?: string;
}

// CSV Workflow response types
export interface PreviewResponse {
  ok: true;
  filePath: string;
  rowCount: number;
  columns: ColSpec[];
  sampleData: any[][];
}

export interface SchemaResponse {
  ok: true;
  schema: Schema;
}

export interface PatchResponse {
  ok: true;
  updatedColumns: string[];
}

export interface RunnerResponse {
  ok: true;
  script: string;
  scriptPath?: string;
}

export interface ExecutionResponse {
  ok: true;
  stdout: string;
  stderr: string;
  exitCode: number;
}

// Legacy compatibility types
export type LegacyColType = "numeric" | "categorical" | "text";
