#!/usr/bin/env python3
import os
from toorpia.client import toorPIA

# 絶対パスを使用
csv_path = os.path.abspath("biopsy.csv")
print(f"Using CSV file: {csv_path}")
print(f"File exists: {os.path.exists(csv_path)}")

client = toorPIA()

# First, create a base map using basemap_csvform
print("=== Creating base map ===")
base_result = client.basemap_csvform(
    csv_path,
    weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
    type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
    identna_resolution=200,
    identna_effective_radius=0.2
)
print(f"Base result shape: {base_result['xyData'].shape if base_result else 'Failed'}")
print(f"Map No: {base_result['mapNo'] if base_result else 'N/A'}")
print(f"Share URL: {base_result['shareUrl'] if base_result else 'N/A'}")

# Now, add a plot using the same CSV file (this will use stored CSV options)
print("\n=== Adding plot (inherits basemap identna) ===")
addplot_result1 = client.addplot_csvform(
    csv_path,  # Same CSV file for addplot
    detabn_max_window=5,
    detabn_rate_threshold=1.0,
    detabn_threshold=0,
    detabn_print_score=True
)
print(f"Addplot result 1: {addplot_result1}")
if addplot_result1:
    print(f"Add Plot No: {addplot_result1.get('addPlotNo')}")
    print(f"Abnormality Status: {addplot_result1.get('abnormalityStatus')}")
    print(f"Abnormality Score: {addplot_result1.get('abnormalityScore')}")
    print(f"Share URL with addplot: {addplot_result1.get('shareUrl')}")

# Add another plot with custom identna parameters
print("\n=== Adding plot with custom identna parameters ===")
addplot_result2 = client.addplot_csvform(
    csv_path,  # Same CSV file for addplot
    identna_resolution=100,      # Custom identna resolution (different from basemap)
    identna_effective_radius=0.1, # Custom effective radius (different from basemap)
    detabn_max_window=3,
    detabn_rate_threshold=0.8,
    detabn_threshold=0,
    detabn_print_score=True
)
print(f"Addplot result 2: {addplot_result2}")
if addplot_result2:
    print(f"Add Plot No: {addplot_result2.get('addPlotNo')}")
    print(f"Abnormality Status: {addplot_result2.get('abnormalityStatus')}")
    print(f"Abnormality Score: {addplot_result2.get('abnormalityScore')}")
    print(f"Share URL with addplot: {addplot_result2.get('shareUrl')}")
    print(f"Custom identna parameters will create a 'custom' source entry in the database")