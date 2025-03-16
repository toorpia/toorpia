# toorpia API Client

## Installation

To install the toorpia API client, use the following command:

```bash
pip install git+https://github.com/toorpia/toorpia.git
```

## Usage

### Creating a Client

```python
from toorpia import toorPIA

# Create a client using the default API key from environment variable
toorpia_client = toorPIA()

# Or, specify a custom API key
# toorpia_client = toorPIA(api_key=your_api_key)
```

### Basic Operations

#### 1. Creating a Base Map

```python
import pandas as pd

df = pd.read_csv("input.csv")
# Basic usage
results = toorpia_client.fit_transform(df)

# Extended usage with metadata
results = toorpia_client.fit_transform(
    data=df,
    label="Production Line 1 - Pressure Gauge",  # Optional: Name to identify the target equipment
    tag="Pressure Sensor",  # Optional: Classification category for the map
    description="Pressure gauge used in the 3rd process of Production Line 1. Model: ABC-123",  # Optional: Detailed description
    random_seed=123  # Optional: Random seed for clustering (default: 42)
)

print(toorpia_client.shareUrl)  # Get the share URL for the created map
```

#### 2. Adding Data to an Existing Map

```python
df_add = pd.read_csv("add.csv")

# Using the most recent map
results_add = toorpia_client.addplot(df_add)
print(toorpia_client.shareUrl)  # Get the share URL for the updated map
print(toorpia_client.currentAddPlotNo)  # Get the add plot number

# Using a specific map number
results_add = toorpia_client.addplot(df_add, 123)

# Using a map from a directory
results_add = toorpia_client.addplot(df_add, "/path/to/basemap/data/directory")
```

#### 3. Working with Add Plot History

toorPIA now supports maintaining a history of add plots for each map. This allows you to track multiple add plot operations and access their results at any time.

```python
# List all add plots for a specific map
add_plots = toorpia_client.list_addplots(toorpia_client.mapNo)
print(f"Found {len(add_plots)} add plots for this map")

# Get a specific add plot by its number
add_plot_info = toorpia_client.get_addplot(toorpia_client.mapNo, 1)  # Get the first add plot

# Access the add plot data
xy_data = add_plot_info['xyData']  # NumPy array of coordinates
add_plot_metadata = add_plot_info['addPlot']  # Metadata about the add plot
share_url = add_plot_info['shareUrl']  # Share URL for this specific add plot

# Iterate through all add plots
if add_plots:
    for add_plot in add_plots:
        print(f"Add Plot #{add_plot['addPlotNo']} created at {add_plot['createdAt']}")
        print(f"Records: {add_plot['nRecord']}")
```

#### 4. Listing Available Maps

```python
map_list = toorpia_client.list_map()
```

#### 4. Exporting a Map

```python
map_no = toorpia_client.mapNo  # Or any valid map number
toorpia_client.export_map(map_no, "/path/to/export/directory")
```

#### 5. Importing a Map

```python
new_map_no = toorpia_client.import_map("/path/to/import/directory")
```

### Share URL Feature

Each operation that modifies a map (fit_transform, addplot, etc.) generates a share URL that can be accessed through the `shareUrl` property of the client. This URL provides access to a graphical user interface where you can visually inspect and interact with the map data.

Example of accessing the share URL:
```python
# After creating or modifying a map
print(toorpia_client.shareUrl)
# Output: http://localhost:3000/map-inspector?seg=rawdata.csv&segHash=...
```

The share URL includes:
- Links to the map data files (rawdata.csv, xy.dat, etc.)
- Hash values for data integrity verification
- Additional parameters for any added data (when using addplot)

Opening this URL in a web browser will display an interactive visualization of your map data, allowing you to:
- View the data distribution
- Inspect data points
- Analyze patterns and relationships in the data

## Environment Configuration

### API Key

Set your API key using the `TOORPIA_API_KEY` environment variable:

- Unix/Linux/macOS:
  ```
  export TOORPIA_API_KEY='your-valid-api-key'
  ```

- Windows:
  ```
  set TOORPIA_API_KEY=your-valid-api-key
  ```

### API Server URL (for on-premise users)

Set the API server URL using the `TOORPIA_API_URL` environment variable:

- Unix/Linux/macOS:
  ```
  export TOORPIA_API_URL='http://your-ip-address:3000'
  ```

- Windows:
  ```
  set TOORPIA_API_URL=http://your-ip-address:3000
  ```

## Advanced Features

### Checksum Calculation and Comparison

The client automatically calculates checksums for map data during import and export operations. This ensures data integrity and prevents unnecessary uploads of duplicate data.

### Flexible Map Selection in addplot

The `addplot` method now supports flexible arguments:

- No additional argument: Uses the most recent map
- Integer argument: Uses the specified map number
- String argument: Uses the map data from the specified directory

Example:
```python
toorpia_client.addplot(data)  # Uses most recent map
toorpia_client.addplot(data, 123)  # Uses map number 123
toorpia_client.addplot(data, "/path/to/map")  # Uses map data from the specified directory
```

### Add Plot History Features

The client now maintains a history of all add plot operations for each map:

1. **Tracking Add Plot Numbers**: Each add plot operation receives a unique number within its map, accessible via the `currentAddPlotNo` property.

2. **Listing Add Plots**: Use `list_addplots(map_no)` to retrieve all add plots for a specific map.

3. **Retrieving Specific Add Plots**: Use `get_addplot(map_no, addplot_no)` to fetch details about a specific add plot, including its coordinates and metadata.

These features enable more sophisticated analysis workflows, such as:
- Comparing multiple datasets against the same base map
- Tracking changes in data over time
- Building a history of analysis operations for better reproducibility

## Error Handling

The client provides informative error messages for various scenarios, including authentication failures, invalid requests, and server errors. Always check the return values and handle potential errors in your code.

## Performance Considerations

- Map exports may take some time, especially for large datasets.
- For `addplot` operations, consider performance implications when working with large map data directories.

## Function Aliases

For convenience, some functions have aliases:

- `import_map` can also be called as `upload_map`
- `export_map` can also be called as `download_map`

These aliases provide the same functionality as their original counterparts and can be used interchangeably.

For more detailed information about specific methods and their parameters, refer to the inline documentation in the source code.
