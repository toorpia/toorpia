#!/usr/bin/env python3
"""
Test script for the add plot history features of the toorPIA client.
This script demonstrates:
1. Creating a base map
2. Adding multiple add plots to the same map
3. Listing all add plots for a map
4. Retrieving specific add plot information
"""

import os
import sys
import pandas as pd
import numpy as np
from toorpia import toorPIA

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def main():
    # Set environment variables if not already set
    # You can also set these in your shell before running the script
    if not os.environ.get('TOORPIA_API_URL'):
        os.environ['TOORPIA_API_URL'] = 'http://localhost:3000'
    
    print_separator("1. Initializing toorPIA Client")
    client = toorPIA()
    print("Client initialized.\n")

    # Load sample data
    print_separator("2. Loading Sample Data")
    base_data_path = os.path.join(os.path.dirname(__file__), 'biopsy.csv')
    add_data_path = os.path.join(os.path.dirname(__file__), 'biopsy-add.csv')
    
    if not os.path.exists(base_data_path) or not os.path.exists(add_data_path):
        print(f"Error: Sample data files not found in {os.path.dirname(__file__)}")
        print(f"Looked for: {base_data_path} and {add_data_path}")
        return 1
    
    base_data = pd.read_csv(base_data_path)
    add_data = pd.read_csv(add_data_path)
    
    print(f"Base data loaded: {base_data.shape[0]} rows, {base_data.shape[1]} columns")
    print(f"Add data loaded: {add_data.shape[0]} rows, {add_data.shape[1]} columns\n")

    # Create base map
    print_separator("3. Creating Base Map")
    try:
        result = client.fit_transform(base_data)
        print(f"Base map created successfully. Map No: {client.mapNo}")
        print(f"Share URL: {client.shareUrl}\n")
    except Exception as e:
        print(f"Error creating base map: {str(e)}")
        return 1

    # Create first add plot
    print_separator("4. Creating First Add Plot")
    try:
        add_result_1 = client.addplot(add_data)
        print(f"First add plot created. Add Plot No: {client.currentAddPlotNo}")
        print(f"Share URL: {client.shareUrl}")
        print(f"Result shape: {add_result_1.shape}\n")
    except Exception as e:
        print(f"Error creating first add plot: {str(e)}")
        return 1

    # Create second add plot
    print_separator("5. Creating Second Add Plot")
    try:
        add_result_2 = client.addplot(add_data)
        print(f"Second add plot created. Add Plot No: {client.currentAddPlotNo}")
        print(f"Share URL: {client.shareUrl}")
        print(f"Result shape: {add_result_2.shape}\n")
    except Exception as e:
        print(f"Error creating second add plot: {str(e)}")
        return 1

    # List all add plots
    print_separator("6. Listing All Add Plots")
    try:
        add_plots = client.list_addplots(client.mapNo)
        print(f"Found {len(add_plots)} add plots for map {client.mapNo}")
        
        if add_plots:
            for add_plot in add_plots:
                print(f"\nAdd Plot #{add_plot['addPlotNo']}:")
                print(f"  Created at: {add_plot['createdAt']}")
                print(f"  Records: {add_plot['nRecord']}")
                print(f"  Files: {add_plot['segmentFile']}, {add_plot['xyFile']}")
                print(f"  Share URL: {add_plot.get('shareUrl', 'N/A')}")
    except Exception as e:
        print(f"Error listing add plots: {str(e)}")
        return 1

    # Get specific add plot
    print_separator("7. Getting Specific Add Plot")
    try:
        add_plot_info = client.get_addplot(client.mapNo, 1)  # Get the first add plot
        print(f"Retrieved add plot 1 information:")
        print(f"  Metadata: {add_plot_info['addPlot']}")
        print(f"  XY Data Shape: {add_plot_info['xyData'].shape}")
        print(f"  Share URL: {add_plot_info['shareUrl']}\n")
    except Exception as e:
        print(f"Error getting specific add plot: {str(e)}")
        return 1

    # Test error case - non-existent add plot
    print_separator("8. Testing Error Case - Non-existent Add Plot")
    try:
        non_existent_plot = client.get_addplot(client.mapNo, 999)  # This should not exist
        if non_existent_plot is None:
            print("Test passed: Correctly returned None for non-existent add plot\n")
        else:
            print("Test failed: Should have returned None for non-existent add plot\n")
    except Exception as e:
        print(f"Exception while testing non-existent add plot: {str(e)}\n")

    print_separator("Test Completed Successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
