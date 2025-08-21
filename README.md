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

#### 1. Creating a Base Map from CSV (Table) Data

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

##### Advanced: Custom identna Parameters

You can customize the normal area identification (identna) parameters when creating a base map:

```python
results = toorpia_client.fit_transform(
    data=df,
    identna_resolution=50,        # Mesh resolution (default: 100)
    identna_effective_radius=0.15 # Effective radius ratio (default: 0.1)
)
```

**identna Parameters:**
- `identna_resolution`: Mesh resolution for normal area identification. Higher values provide finer granularity but require more computation.
- `identna_effective_radius`: Effective radius as a ratio to the mesh area side length. Controls the influence radius around each data point.

#### 2. Creating a Base Map from WAV (Sound) Data

```python
# Single WAV file processing
results = toorpia_client.fit_transform_waveform(["audio_data.wav"])
print(f"Map Number: {toorpia_client.mapNo}")
print(f"Share URL: {toorpia_client.shareUrl}")

# Multiple WAV files processing
wav_files = ["audio1.wav", "audio2.wav", "audio3.wav"]
results = toorpia_client.fit_transform_waveform(wav_files)

# Advanced parameter customization
results = toorpia_client.fit_transform_waveform(
    files=["machine_sound.wav"],
    mkfftseg_hp=100.0,        # High-pass filter: cut frequencies below 100Hz
    mkfftseg_lp=8000.0,       # Low-pass filter: cut frequencies above 8kHz
    mkfftseg_wl=32768,        # Window length: 32768 samples
    mkfftseg_wf="hamming",    # Window function: Hamming window
    mkfftseg_ol=75.0,         # Overlap ratio: 75%
    identna_resolution=50,    # Mesh resolution: 50
    label="Machine Sound Analysis",
    tag="Acoustic Monitoring"
)

# Mixed processing with WAV and CSV files
mixed_files = ["vibration_data.csv", "audio_data.wav"]
results = toorpia_client.fit_transform_waveform(
    files=mixed_files,
    mkfftseg_sr=44100,        # Sample rate for CSV files
    mkfftseg_di=3             # Use 3rd column of CSV as amplitude data
)
```

##### mkfftSeg Parameters

- `mkfftseg_di` (int): Data Index for CSV files (starting from 1, default: 1)
- `mkfftseg_hp` (float): High-pass filter frequency in Hz (-1 to disable, default: -1.0)
- `mkfftseg_lp` (float): Low-pass filter frequency in Hz (-1 to disable, default: -1.0)
- `mkfftseg_nm` (int): Moving average window size (0 for auto-setting, default: 0)
- `mkfftseg_ol` (float): Overlap ratio as percentage (default: 50.0)
- `mkfftseg_sr` (int): Sample rate for CSV files (default: 48000)
- `mkfftseg_wf` (str): Window function - "hanning" or "hamming" (default: "hanning")
- `mkfftseg_wl` (int): Window length in samples (default: 65536)

**Note**: For WAV files, the sample rate is automatically detected from the file header. For CSV files, you must specify the sample rate using `mkfftseg_sr` parameter.

#### 3. Adding Data to an Existing Map

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

##### Advanced: Custom detabn Parameters for Abnormality Detection

You can customize the abnormality detection (detabn) parameters when adding data:

```python
result = toorpia_client.addplot(
    df_add,
    detabn_max_window=3,        # Maximum window size (default: 5)
    detabn_rate_threshold=0.5,  # Abnormality rate threshold (default: 1.0)
    detabn_threshold=0.1,       # Normal area threshold (default: 0)
    detabn_print_score=True     # Print score information (default: True)
)

# Access abnormality detection results
print(f"Abnormality Status: {result['abnormalityStatus']}")  # 'normal', 'abnormal', or 'unknown'
print(f"Abnormality Score: {result['abnormalityScore']}")    # Numerical score
print(f"XY Data: {result['xyData'].shape}")                  # NumPy array of coordinates
```

**detabn Parameters:**
- `detabn_max_window`: Maximum number of sequential data points used for abnormality rate calculation
- `detabn_rate_threshold`: Lower threshold for abnormality rate (0.0 < rate <= 1.0). If rate >= threshold, data is considered abnormal
- `detabn_threshold`: Threshold for relative normal area value. If value > threshold, the point is considered normal
- `detabn_print_score`: Whether to include detailed score information in the analysis

**Return Value Enhancement:**
The `addplot` method now returns a dictionary containing:
- `xyData`: NumPy array of coordinate data
- `addPlotNo`: Sequential number of the add plot
- `abnormalityStatus`: 'normal', 'abnormal', or 'unknown'
- `abnormalityScore`: Numerical abnormality score
- `shareUrl`: Share URL for the updated map

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
        print(f"Status: {add_plot.get('status', 'Unknown')}")  # Display normal/abnormal determination result
```

#### 4. Listing Available Maps

```python
map_list = toorpia_client.list_map()

# Display metadata from the map list
for map_item in map_list:
    print(f"Map #{map_item['mapNo']}: {map_item.get('label', 'No label')}")
    print(f"  Tag: {map_item.get('tag', 'No tag')}")
    print(f"  Records: {map_item['nRecord']}")
    print(f"  Description: {map_item.get('description', 'No description')}")
```

The returned map data includes the following metadata in addition to the basic identification information:
- `label`: Display name of the map
- `tag`: Classification tag for the map
- `description`: Detailed description of the map
You can use these metadata to efficiently organize and search for maps.

#### 4. Exporting a Map

```python
map_no = toorpia_client.mapNo  # Or any valid map number
toorpia_client.export_map(map_no, "/path/to/export/directory")
```

**Important Note**: The export operation only includes base map files. Add plot files are excluded from the export. If your map includes add plots, you'll need to recreate them after importing the map.

#### 5. Importing a Map

```python
new_map_no = toorpia_client.import_map("/path/to/import/directory")
```

**Important Note**: The import operation only processes base map files. Any add plot files in the directory will be ignored. After importing a map, you must recreate any add plots using the `addplot` method.

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

**Note about checksums**: The checksum calculation now excludes add plot files and log files. Only base map files (including clustering-related files) are considered when computing checksums. This ensures consistent checksums for the same base map, regardless of any add plot operations performed.

### Base Map Types

toorPIA supports two types of base maps:

1. **Standard Analysis Maps**: Include simple files like `segments.csv`, `xy.dat`, `status.mi`, and `rawdata.csv`.

2. **Clustering Analysis Maps**: Generated for larger datasets, these include additional files:
   - Seed files (`seed-segments.csv`, `seed-xy.dat`)
   - Multiple cluster files (`raw-x*.csv`, `segments-x*.csv`, `xy-x*.dat`)
   - Header files and other clustering data

Export and import operations handle both types appropriately, preserving all necessary files for the base map while excluding add plot data.

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
