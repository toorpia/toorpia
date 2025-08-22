// Common type definitions for toorPIA MCP server

export type ColType = "numeric" | "categorical" | "text";

export interface ColSpec {
  name: string;
  type: ColType;
  description?: string;
}

export interface Schema {
  columns: ColSpec[];
  description?: string;
}

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
