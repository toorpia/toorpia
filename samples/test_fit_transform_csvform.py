#!/usr/bin/env python3
import os
from toorpia.client import toorPIA

# 絶対パスを使用
csv_path = os.path.abspath("biopsy.csv")
print(f"Using CSV file: {csv_path}")
print(f"File exists: {os.path.exists(csv_path)}")

client = toorPIA()
result = client.fit_transform_csvform(
    csv_path,
#    drop_columns=["No", "ID", "Diagnosis"],
    weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
    type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
    identna_resolution=200,
    identna_effective_radius=0.2
)
print(f"Result: {result}")
print(f"Share URL: {client.shareUrl}")
