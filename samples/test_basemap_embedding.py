#!/usr/bin/env python3
"""
Example: Using the basemap_embedding / addplot_embedding API for embedding vectors

This example generates synthetic embeddings with numpy (no data files needed),
creates a base map with basemap_embedding(), and tests new data against it with
addplot_embedding(). Embedding preprocessing (L2 normalization, ID column
detection) is handled server-side; addplot inherits the basemap's settings
automatically, so no preprocessing options are needed (or allowed) on addplot.

The API key is taken from the TOORPIA_API_KEY environment variable
(and the server URL from TOORPIA_API_URL for on-premise environments).
"""
import numpy as np
from toorpia import toorPIA


def main():
    # Initialize client (uses TOORPIA_API_KEY / TOORPIA_API_URL environment variables)
    client = toorPIA()

    # Generate synthetic embeddings: 200 samples x 32 dimensions for the base map
    rng = np.random.default_rng(42)
    base_embeddings = rng.normal(size=(200, 32))
    print(f"Base embeddings shape: {base_embeddings.shape}")

    # New data for addplot: 50 samples from the same distribution,
    # plus 10 shifted samples that should look anomalous
    normal_add = rng.normal(size=(50, 32))
    shifted_add = rng.normal(loc=3.0, size=(10, 32))
    add_embeddings = np.vstack([normal_add, shifted_add])
    print(f"Addplot embeddings shape: {add_embeddings.shape}")

    # === Step 1: Create base map from the embedding vectors ===
    # ndarray input is uploaded as a headerless CSV; dimension names are
    # auto-generated server-side and stay consistent between basemap and addplot.
    print("\n=== Creating embedding base map ===")
    result = client.basemap_embedding(
        base_embeddings,
        label="Synthetic Embedding Baseline",
        tag="Embedding Demo",
        description="200 x 32 synthetic normal embeddings"
    )
    if result is None:
        print("❌ Base map creation failed")
        return
    print(f"✅ Base map created!")
    print(f"Map Number: {result['mapNo']}")
    print(f"Coordinate Data Shape: {result['xyData'].shape}")
    print(f"Share URL: {result['shareUrl']}")

    # === Step 2: Add new embeddings for anomaly detection ===
    # l2_normalization / id_columns must NOT be specified here:
    # they are inherited from the basemap on the server side.
    print("\n=== Adding embeddings for anomaly detection ===")
    addplot_result = client.addplot_embedding(
        add_embeddings,
        detabn_max_window=5,
        detabn_rate_threshold=1.0,
        detabn_threshold=0,
        detabn_print_score=True
    )
    if addplot_result is None:
        print("❌ Addplot failed")
        return
    print(f"✅ Addplot completed!")
    print(f"Addplot Number: {addplot_result['addPlotNo']}")
    print(f"Addplot Data Shape: {addplot_result['xyData'].shape}")
    print(f"Abnormality Status: {addplot_result['abnormalityStatus']}")
    if addplot_result.get('abnormalityScore') is not None:
        print(f"Abnormality Score: {addplot_result['abnormalityScore']:.4f}")
    print(f"Updated Share URL: {addplot_result['shareUrl']}")

    # Visual analysis instructions
    print(f"\n🌐 Open in browser for visual analysis:")
    print(f"   {addplot_result['shareUrl']}")


if __name__ == "__main__":
    main()
