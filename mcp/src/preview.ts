import { createReadStream, existsSync, statSync } from "node:fs";
import { createGunzip } from "node:zlib";
import { Readable } from "node:stream";
import { parse } from "csv-parse";
import { ToolError } from "./errors.js";

export interface PreviewResult {
  ok: true;
  filePath: string;
  fileSizeBytes: number;
  rowCount: number;
  columnCount: number;
  headerDetected: boolean;
  headerSample: string[] | null;
  idColumnsDetected: number;
  embeddingDimensions: number;
  l2NormStats: {
    sampledRows: number;
    min: number;
    mean: number;
    max: number;
    coefficientOfVariation: number;
    looksL2Normalized: boolean;
  } | null;
  sampleRows: unknown[][];
  warnings: string[];
  recommendation: string;
}

const NORM_SAMPLE_LIMIT = 10000;
const CONSISTENCY_CHECK_ROWS = 200;
const SAMPLE_DIMS_SHOWN = 6;

function isNumericCell(v: string): boolean {
  const t = v.trim();
  return t !== "" && !Number.isNaN(Number(t));
}

function sig4(v: number): number {
  if (!Number.isFinite(v) || v === 0) return v;
  return Number(v.toPrecision(4));
}

function leadingNonNumeric(row: string[]): number {
  let k = 0;
  while (k < row.length && !isNumericCell(row[k])) k++;
  // A row that is entirely non-numeric is not an ID-column signal (likely a
  // malformed or text row); treat it as zero ID columns here.
  return k === row.length ? 0 : k;
}

export async function previewEmbeddingCsv(path: string, sampleRowCount: number): Promise<PreviewResult> {
  if (!existsSync(path)) {
    throw new ToolError(
      "FILE_NOT_FOUND",
      `File not found: ${path}. Use an absolute path. Ask the user for the correct location of the embedding CSV file.`,
    );
  }
  const lower = path.toLowerCase();
  if (!lower.endsWith(".csv") && !lower.endsWith(".csv.gz")) {
    throw new ToolError(
      "UNSUPPORTED_FILE_TYPE",
      `Unsupported file type: ${path}. Only .csv and .csv.gz files are supported. Ask the user to export the embeddings as CSV (rows = samples, columns = embedding dimensions).`,
    );
  }
  const fileSizeBytes = statSync(path).size;

  let source: Readable = createReadStream(path);
  if (lower.endsWith(".csv.gz")) {
    const gunzip = createGunzip();
    source.pipe(gunzip);
    source.on("error", (e) => gunzip.destroy(e));
    source = gunzip;
  }

  const parser = parse({ bom: true, relax_column_count: true, skip_empty_lines: true });
  source.pipe(parser);

  let firstRow: string[] | null = null;
  let headerDetected = false;
  let columnCount = 0;
  let idColumnsDetected = 0;
  let idColumnsLocked = false;
  let rowCount = 0;
  const sampleRows: string[][] = [];
  const warnings: string[] = [];
  let inconsistentColumnRows = 0;
  let nonNumericDimCells = 0;

  let normCount = 0;
  let normMin = Infinity;
  let normMax = -Infinity;
  let normSum = 0;
  let normSumSq = 0;

  try {
    for await (const record of parser as AsyncIterable<string[]>) {
      if (firstRow === null) {
        firstRow = record;
        columnCount = record.length;
        // Header heuristic (mirrors the server's auto-detection intent): a
        // first row whose cells are all non-numeric is a header.
        headerDetected = record.length > 0 && record.every((c) => !isNumericCell(c));
        if (headerDetected) continue;
      }

      rowCount++;
      if (record.length !== columnCount) inconsistentColumnRows++;

      if (!idColumnsLocked) {
        idColumnsDetected = Math.max(idColumnsDetected, leadingNonNumeric(record));
        if (rowCount >= CONSISTENCY_CHECK_ROWS) idColumnsLocked = true;
      }

      if (sampleRows.length < sampleRowCount) {
        sampleRows.push(record);
      }

      if (normCount < NORM_SAMPLE_LIMIT) {
        let sumSq = 0;
        let valid = true;
        for (let i = idColumnsDetected; i < record.length; i++) {
          const v = Number(record[i]);
          if (Number.isNaN(v)) {
            nonNumericDimCells++;
            valid = false;
            break;
          }
          sumSq += v * v;
        }
        if (valid) {
          const norm = Math.sqrt(sumSq);
          normCount++;
          normSum += norm;
          normSumSq += norm * norm;
          if (norm < normMin) normMin = norm;
          if (norm > normMax) normMax = norm;
        }
      }
    }
  } catch (e: any) {
    throw new ToolError(
      "CSV_PARSE_ERROR",
      `Failed to parse ${path} as CSV: ${e?.message ?? e}. Check that the file is a valid ${lower.endsWith(".gz") ? "gzip-compressed " : ""}CSV of embedding vectors.`,
    );
  }

  if (rowCount === 0) {
    throw new ToolError(
      "EMPTY_FILE",
      `No data rows found in ${path}. The file ${headerDetected ? "contains only a header row" : "is empty"}. Check that the embedding export completed correctly.`,
    );
  }

  const embeddingDimensions = columnCount - idColumnsDetected;
  if (inconsistentColumnRows > 0) {
    warnings.push(`${inconsistentColumnRows} row(s) have a different number of columns than the first row (${columnCount}).`);
  }
  if (nonNumericDimCells > 0) {
    warnings.push(
      `${nonNumericDimCells} sampled row(s) contain non-numeric values inside the embedding-dimension region; the server may reject the file or misdetect ID columns.`,
    );
  }
  if (embeddingDimensions <= 1) {
    warnings.push("Only one or zero numeric dimensions detected — this does not look like an embedding matrix.");
  }

  let l2NormStats: PreviewResult["l2NormStats"] = null;
  if (normCount > 0) {
    const mean = normSum / normCount;
    const variance = Math.max(0, normSumSq / normCount - mean * mean);
    const cv = mean > 0 ? Math.sqrt(variance) / mean : 0;
    l2NormStats = {
      sampledRows: normCount,
      min: sig4(normMin),
      mean: sig4(mean),
      max: sig4(normMax),
      coefficientOfVariation: sig4(cv),
      looksL2Normalized: mean > 0 && Math.abs(normMin - 1) < 0.01 && Math.abs(normMax - 1) < 0.01,
    };
  }

  let recommendation: string;
  if (l2NormStats?.looksL2Normalized) {
    recommendation =
      "Vectors are already L2-normalized; the server default (l2_normalization: true) is fine and idempotent.";
  } else if (l2NormStats && l2NormStats.coefficientOfVariation > 0.1) {
    recommendation =
      `Vector norms vary noticeably (CV=${l2NormStats.coefficientOfVariation}). By default the server L2-normalizes every vector, which discards magnitude. If magnitude carries meaning for this data, pass l2_normalization: false to create_basemap; otherwise the default is fine.`;
  } else {
    recommendation = "The server default preprocessing (L2 normalization, auto ID-column detection) should work for this file.";
  }
  if (idColumnsDetected > 0) {
    recommendation += ` The first ${idColumnsDetected} column(s) look like ID/label columns; the server should auto-detect them, so id_columns usually does not need to be set.`;
  }

  const truncateRow = (row: string[]): unknown[] => {
    const ids = row.slice(0, idColumnsDetected);
    const dims = row.slice(idColumnsDetected, idColumnsDetected + SAMPLE_DIMS_SHOWN).map((v) => {
      const n = Number(v);
      return Number.isNaN(n) ? v : sig4(n);
    });
    const hidden = row.length - idColumnsDetected - dims.length;
    return hidden > 0 ? [...ids, ...dims, `... (+${hidden} more dims)`] : [...ids, ...dims];
  };

  return {
    ok: true,
    filePath: path,
    fileSizeBytes,
    rowCount,
    columnCount,
    headerDetected,
    headerSample: headerDetected && firstRow ? (truncateRow(firstRow) as string[]) : null,
    idColumnsDetected,
    embeddingDimensions,
    l2NormStats,
    sampleRows: sampleRows.map(truncateRow),
    warnings,
    recommendation,
  };
}
