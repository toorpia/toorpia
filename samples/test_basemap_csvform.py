#!/usr/bin/env python3
"""
Example: Using the basemap_csvform API for creating base maps from CSV files

This example demonstrates both detailed and simple usage patterns of the unified API 
that returns structured data including coordinate data, map numbers, and share URLs.
"""
import os
from toorpia.client import toorPIA

def detailed_example():
    """Comprehensive example with detailed addplot parameters and output"""
    # Initialize client
    client = toorPIA()
    
    # CSV file path
    csv_path = os.path.abspath("biopsy.csv")
    print(f"Using CSV file: {csv_path}")
    print(f"File exists: {os.path.exists(csv_path)}")
    
    # Create base map using the new unified API
    print("\n=== Creating Base Map (Detailed) ===")
    result = client.basemap_csvform(
        csv_path,
        # Optional: drop columns that are not needed for analysis
        # drop_columns=["No", "ID", "Diagnosis"],
        weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
        type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
        identna_resolution=200,
        identna_effective_radius=0.2,
        label="Breast Cancer Biopsy Analysis",
        tag="Medical Diagnostics",
        description="Wisconsin breast cancer diagnostic features dataset"
    )
    
    if result:
        print(f"✅ Base map created successfully!")
        print(f"Map Number: {result['mapNo']}")
        print(f"Coordinate Data Shape: {result['xyData'].shape}")
        print(f"Share URL: {result['shareUrl']}")
        
        # Add new data for anomaly detection with detailed parameters
        print("\n=== Adding Data for Anomaly Detection (Detailed) ===")
        addplot_result = client.addplot_csvform(
            csv_path,
            detabn_max_window=5,
            detabn_rate_threshold=1.0,
            detabn_threshold=0,
            detabn_print_score=True
        )
        
        if addplot_result:
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
            print(f"\n📊 In the Map Inspector, you can:")
            print(f"   • View the base map (green points)")
            print(f"   • See addplot data (red × marks if anomalous)")
            print(f"   • Interactive data exploration and filtering")
            
        else:
            print("❌ Addplot failed")
    else:
        print("❌ Base map creation failed")

def simple_example():
    """Simple quick-start example with minimal parameters"""
    print("\n" + "="*50)
    print("SIMPLE USAGE EXAMPLE")
    print("="*50)
    
    # Initialize client
    client = toorPIA()
    
    # CSV file path
    csv_path = os.path.abspath("biopsy.csv")
    print(f"Using CSV file: {csv_path}")
    print(f"File exists: {os.path.exists(csv_path)}")
    
    # Create base map using minimal parameters
    print("\n--- Creating Base Map (Simple) ---")
    result = client.basemap_csvform(
        csv_path,
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
        
        # Simple addplot functionality
        print("\n--- Testing addplot functionality (Simple) ---")
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

def main():
    """Main function demonstrating both usage patterns"""
    print("basemap_csvform API Examples")
    print("=" * 40)
    print("This script demonstrates two usage patterns:")
    print("1. Detailed example with comprehensive error handling and visualization instructions")
    print("2. Simple example for quick start")
    print()
    
    # Run detailed example by default
    detailed_example()
    
    # Uncomment the line below to also run the simple example
    # simple_example()

if __name__ == "__main__":
    main()