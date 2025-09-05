#!/usr/bin/env python3
import os
from toorpia.client import toorPIA

# 絶対パスを使用
csv_path = os.path.abspath("biopsy.csv")
print(f"Using CSV file: {csv_path}")
print(f"File exists: {os.path.exists(csv_path)}")

client = toorPIA()

# First, create a base map using fit_transform_csvform
print("=== Creating base map ===")
base_result = client.fit_transform_csvform(
    csv_path,
    weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
    type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
    identna_resolution=200,
    identna_effective_radius=0.2
)
print(f"Base result: {base_result}")
print(f"Map No: {client.mapNo}")
print(f"Share URL: {client.shareUrl}")

# Now, add a plot using the same CSV file (this will use stored CSV options)
print("\n=== Adding plot ===")
addplot_result = client.addplot_csvform(
    csv_path,  # Same CSV file for addplot
    detabn_max_window=5,
    detabn_rate_threshold=1.0,
    detabn_threshold=0,
    detabn_print_score=True
)
print(f"Addplot result: {addplot_result}")
if addplot_result:
    print(f"Add Plot No: {addplot_result.get('addPlotNo')}")
    print(f"Abnormality Status: {addplot_result.get('abnormalityStatus')}")
    print(f"Abnormality Score: {addplot_result.get('abnormalityScore')}")
    print(f"Share URL with addplot: {addplot_result.get('shareUrl')}")