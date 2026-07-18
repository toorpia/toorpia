// Unified error type for tool responses.
// `reason` is written for the AI client: it states what went wrong AND what to
// do next, so the model can self-correct or give the user precise instructions.
export class ToolError extends Error {
  constructor(
    public readonly code: string,
    public readonly reason: string,
  ) {
    super(reason);
    this.name = "ToolError";
  }
}

export interface ErrorPayload {
  [key: string]: unknown;
  ok: false;
  code: string;
  reason: string;
}

export function toErrorPayload(error: unknown): ErrorPayload {
  if (error instanceof ToolError) {
    return { ok: false, code: error.code, reason: error.reason };
  }
  const message = error instanceof Error ? error.message : String(error);
  return {
    ok: false,
    code: "INTERNAL_ERROR",
    reason: `Unexpected error: ${message}. If this persists, ask the user to report it with the exact tool input used.`,
  };
}
