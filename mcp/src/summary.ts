// Compact statistical summary of a 2-D coordinate cloud, computed locally from
// the API's baseXyData so the full point list never enters the model context.

export interface XySummary {
  nPoints: number;
  xRange: [number, number];
  yRange: [number, number];
  centroid: [number, number];
  radiusOfGyration: number;
  outlierCandidates: { count: number; ratio: number; note: string };
  clusterEstimate: { count: number; note: string };
}

function sig4(v: number): number {
  if (!Number.isFinite(v) || v === 0) return v;
  return Number(v.toPrecision(4));
}

export function summarizeXy(xy: number[][]): XySummary | null {
  const pts = xy.filter((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  const n = pts.length;
  if (n === 0) return null;

  let sx = 0;
  let sy = 0;
  let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
  for (const [x, y] of pts) {
    sx += x;
    sy += y;
    if (x < xMin) xMin = x;
    if (x > xMax) xMax = x;
    if (y < yMin) yMin = y;
    if (y > yMax) yMax = y;
  }
  const cx = sx / n;
  const cy = sy / n;

  let sumSq = 0;
  for (const [x, y] of pts) {
    sumSq += (x - cx) ** 2 + (y - cy) ** 2;
  }
  const rg = Math.sqrt(sumSq / n);

  const threshold = 2 * rg;
  let outliers = 0;
  if (rg > 0) {
    for (const [x, y] of pts) {
      if (Math.hypot(x - cx, y - cy) > threshold) outliers++;
    }
  }

  return {
    nPoints: n,
    xRange: [sig4(xMin), sig4(xMax)],
    yRange: [sig4(yMin), sig4(yMax)],
    centroid: [sig4(cx), sig4(cy)],
    radiusOfGyration: sig4(rg),
    outlierCandidates: {
      count: outliers,
      ratio: sig4(outliers / n),
      note: "points farther than 2 x radiusOfGyration from the centroid",
    },
    clusterEstimate: estimateClusters(pts, xMin, xMax, yMin, yMax),
  };
}

/**
 * Rough cluster-count estimate: rasterize points onto a grid and count
 * 8-connected components of occupied cells, ignoring components that hold a
 * negligible share of the points. Intentionally simple — it signals "one blob
 * vs. several groups", not a rigorous clustering.
 */
function estimateClusters(
  pts: number[][],
  xMin: number,
  xMax: number,
  yMin: number,
  yMax: number,
): { count: number; note: string } {
  const note = "rough grid-density estimate; inspect the shareUrl for the actual structure";
  const G = 40;
  const w = xMax - xMin;
  const h = yMax - yMin;
  if (w === 0 && h === 0) return { count: 1, note };

  const cellOf = (x: number, y: number): number => {
    const i = Math.min(G - 1, Math.max(0, w === 0 ? 0 : Math.floor(((x - xMin) / w) * G)));
    const j = Math.min(G - 1, Math.max(0, h === 0 ? 0 : Math.floor(((y - yMin) / h) * G)));
    return j * G + i;
  };

  const counts = new Map<number, number>();
  for (const [x, y] of pts) {
    const c = cellOf(x, y);
    counts.set(c, (counts.get(c) ?? 0) + 1);
  }

  // Flood-fill 8-connected components over occupied cells.
  const seen = new Set<number>();
  const componentSizes: number[] = [];
  for (const start of counts.keys()) {
    if (seen.has(start)) continue;
    let size = 0;
    const stack = [start];
    seen.add(start);
    while (stack.length) {
      const cell = stack.pop()!;
      size += counts.get(cell)!;
      const ci = cell % G;
      const cj = Math.floor(cell / G);
      for (let dj = -1; dj <= 1; dj++) {
        for (let di = -1; di <= 1; di++) {
          if (di === 0 && dj === 0) continue;
          const ni = ci + di;
          const nj = cj + dj;
          if (ni < 0 || ni >= G || nj < 0 || nj >= G) continue;
          const neighbor = nj * G + ni;
          if (counts.has(neighbor) && !seen.has(neighbor)) {
            seen.add(neighbor);
            stack.push(neighbor);
          }
        }
      }
    }
    componentSizes.push(size);
  }

  const minShare = Math.max(3, pts.length * 0.02);
  const count = componentSizes.filter((s) => s >= minShare).length;
  return { count: Math.max(1, count), note };
}
