#!/usr/bin/env python3
import os
from toorpia.client import toorPIA

# 絶対パスを使用
csv_path = os.path.abspath("biopsy.csv")
print(f"Using CSV file: {csv_path}")
print(f"File exists: {os.path.exists(csv_path)}")

client = toorPIA()

# Using the new unified API (basemap_csvform)
result = client.basemap_csvform(
    csv_path,
#    drop_columns=["No", "ID", "Diagnosis"],
    weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
    type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
    identna_resolution=200,
    identna_effective_radius=0.2,
    label="Biopsy Data Analysis",
    tag="Medical Data",
    description="Breast cancer biopsy diagnostic features"
)

if result:
    print(f"✅ Basemap created successfully!")
    print(f"Coordinates shape: {result['xyData'].shape}")
    print(f"Map number: {result['mapNo']}")
    print(f"Share URL: {result['shareUrl']}")
    
    # Demonstrate addplot functionality  
    print("\n--- Testing addplot functionality ---")
    addplot_result = client.addplot_csvform(csv_path)
    if addplot_result:
        print(f"✅ Addplot created successfully!")
        print(f"Addplot coordinates shape: {addplot_result['xyData'].shape}")
        print(f"Addplot number: {addplot_result['addPlotNo']}")
        print(f"Abnormality status: {addplot_result['abnormalityStatus']}")
        print(f"Abnormality score: {addplot_result.get('abnormalityScore', 'N/A')}")
        print(f"Updated share URL: {addplot_result['shareUrl']}")
    else:
        print("❌ Addplot failed")
else:
    print("❌ Basemap creation failed")
