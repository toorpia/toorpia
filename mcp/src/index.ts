#!/usr/bin/env node
import { startServer } from "./server.js";

startServer().catch((error) => {
  console.error("[toorpia-mcp] failed to start:", error);
  process.exit(1);
});
