# toorPIA API Reference

This document provides detailed specifications for all methods and parameters of the toorPIA Python client library.

## Table of Contents

- [Client Initialization](#client-initialization)
- [Basic Operations](#basic-operations)
- [Data Format Specific Methods](#data-format-specific-methods)
- [Add Plot Methods](#add-plot-methods)
- [Map Management](#map-management)
- [Parameter Details](#parameter-details)
- [Return Values](#return-values)
- [Process Method Compatibility](#process-method-compatibility)

---

## Client Initialization

### toorPIA Class

```python
from toorpia import toorPIA

# Create a client using the default API key from environment variable
client = toorPIA()

# Or, specify a custom API key
client = toorPIA(api_key="your-api-key")
```

#### Environment Variables

- `TOORPIA_API_KEY`: API key for authentication
- `TOORPIA_API_URL`: API server URL for on-premise environments

---

## Basic Operations

### fit_transform()

Creates a base map from pandas DataFrame or numpy array data.

```python
import pandas as pd

df = pd.read_csv("input.csv")

# Basic usage
result = client.fit_transform(df)

# Extended usage with metadata
result = client.fit_transform(
    data=df,
    label="Production Line 1 - Pressure Gauge",  # Optional: Name to identify the target equipment
    tag="Pressure Sensor",  # Optional: Classification category for the map
    description="Pressure gauge used in the 3rd process of Production Line 1. Model: ABC-123",  # Optional: Detailed description
    random_seed=123  # Optional: Random seed for clustering (default: 42)
)

print(client.shareUrl)  # Get the share URL for the created map
```

#### Advanced: Custom identna Parameters

You can customize the normal area identification (identna) parameters when creating a base map:

```python
result = client.fit_transform(
    data=df,
    identna_resolution=50,        # Mesh resolution (default: 100)
    identna_effective_radius=0.15 # Effective radius ratio (default: 0.1)
)
```

**identna Parameters:**
- `identna_resolution`: Mesh resolution for normal area identification. Higher values provide finer granularity but require more computation.
- `identna_effective_radius`: Effective radius as a ratio to the mesh area side length. Controls the influence radius around each data point.

---

## Data Format Specific Methods

### fit_transform_csvform()

Creates a base map by directly processing CSV files without loading them into memory first.

```python
# Basic single CSV file processing
result = client.fit_transform_csvform("sensor_data.csv")
print(f"Map Number: {client.mapNo}")
print(f"Share URL: {client.shareUrl}")

# Multiple CSV files processing (automatically merged)
csv_files = ["data1.csv", "data2.csv", "data3.csv"]
result = client.fit_transform_csvform(csv_files)

# Using drop_columns to exclude specific columns
result = client.fit_transform_csvform(
    "data.csv",
    drop_columns=["ID", "Timestamp", "Comments"]  # These columns will be excluded
)

# Fine control with weight and type options
result = client.fit_transform_csvform(
    "sensor_data.csv",
    weight_option_str="1:0,2:0,3:1,4:1,5:1",  # Columns 1,2 have weight 0
    type_option_str="1:none,2:none,3:float,4:float,5:int"
)

# Complete example with all parameters
result = client.fit_transform_csvform(
    ["train_data.csv", "test_data.csv"],
    drop_columns=["ID", "Name"],  # Takes precedence over weight/type options
    weight_option_str="3:1,4:1,5:1",
    type_option_str="3:float,4:float,5:float",
    identna_resolution=200,
    identna_effective_radius=0.15,
    random_seed=42,
    label="Production Sensor Data",
    tag="Quality Control",
    description="Sensor readings from production line A"
)
```

#### Parameters for CSV Direct Processing

**Column Control Parameters:**
- `weight_option_str` (str): Weight specification for columns using 1-based indexing (e.g., "1:0,2:1,3:1" means column 1 has weight 0, columns 2 and 3 have weight 1)
- `type_option_str` (str): Type specification for columns (e.g., "1:int,2:float,3:enum" specifies column types)
- `drop_columns` (list): List of column names to exclude from processing

**Important:** When `drop_columns` is specified, it takes precedence over `weight_option_str` and `type_option_str`. The dropped columns will automatically be assigned weight=0 and type=none, overriding any manual specifications.

**identna Parameters:**
- `identna_resolution` (int): Mesh resolution for normal area identification (default: 100)
- `identna_effective_radius` (float): Effective radius ratio (default: 0.1)

**Additional Parameters:**
- `random_seed` (int): Random seed for reproducibility (default: 42)
- `label` (str): Display name for the map
- `tag` (str): Classification tag
- `description` (str): Detailed description

**Notes:**
- This method processes CSV files directly without creating a DataFrame, making it efficient for large files
- Single file can be passed as a string, multiple files as a list
- Multiple CSV files are automatically merged into a single map

### fit_transform_waveform()

Creates a base map from WAV (sound) data or CSV time-series data using FFT-based feature extraction.

```python
# Single WAV file processing
result = client.fit_transform_waveform(["audio_data.wav"])
print(f"Map Number: {client.mapNo}")
print(f"Share URL: {client.shareUrl}")

# Multiple WAV files processing
wav_files = ["audio1.wav", "audio2.wav", "audio3.wav"]
result = client.fit_transform_waveform(wav_files)

# Advanced parameter customization
result = client.fit_transform_waveform(
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
result = client.fit_transform_waveform(
    files=mixed_files,
    mkfftseg_sr=44100,        # Sample rate for CSV files
    mkfftseg_di=3             # Use 3rd column of CSV as amplitude data
)
```

#### mkfftSeg Parameters

- `mkfftseg_di` (int): Data Index for CSV files (starting from 1, default: 1)
- `mkfftseg_hp` (float): High-pass filter frequency in Hz (-1 to disable, default: -1.0)
- `mkfftseg_lp` (float): Low-pass filter frequency in Hz (-1 to disable, default: -1.0)
- `mkfftseg_nm` (int): Moving average window size (0 for auto-setting, default: 0)
- `mkfftseg_ol` (float): Overlap ratio as percentage (default: 50.0)
- `mkfftseg_sr` (int): Sample rate for CSV files (default: 48000)
- `mkfftseg_wf` (str): Window function - "hanning" or "hamming" (default: "hanning")
- `mkfftseg_wl` (int): Window length in samples (default: 65536)

**Note**: For WAV files, the sample rate is automatically detected from the file header. For CSV files, you must specify the sample rate using `mkfftseg_sr` parameter.

---

## Add Plot Methods

### addplot()

Adds new data to an existing DataFrame-based map for anomaly detection.

```python
df_add = pd.read_csv("add.csv")

# Using the most recent map
result_add = client.addplot(df_add)
print(client.shareUrl)  # Get the share URL for the updated map
print(client.currentAddPlotNo)  # Get the add plot number

# Using a specific map number
result_add = client.addplot(df_add, 123)

# Using a map from a directory
result_add = client.addplot(df_add, "/path/to/basemap/data/directory")
```

#### Advanced: Custom identna Parameters for Normal Area Generation

You can override the base map's identna parameters for custom normal area generation when adding data:

```python
result = client.addplot(
    df_add,
    identna_resolution=50,          # Custom mesh resolution (default: inherit from basemap)
    identna_effective_radius=0.05   # Custom effective radius (default: inherit from basemap)
)

# When identna parameters are provided:
# - A custom normal area file is generated using these parameters
# - The AddPlot record shows source='custom' for parameter tracking
# - If not provided, parameters are inherited from the basemap with source='basemap'
```

#### Advanced: Custom detabn Parameters for Abnormality Detection

You can customize the abnormality detection (detabn) parameters when adding data:

```python
result = client.addplot(
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

**identna Parameters:**
- `identna_resolution`: Custom mesh resolution for normal area generation (integer). If not provided, inherits from basemap
- `identna_effective_radius`: Custom effective radius for normal area generation (float). If not provided, inherits from basemap
- When custom identna parameters are provided, a new normal area file is generated and the parameter source is recorded as 'custom' for tracking purposes

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

### addplot_waveform()

For WAV and CSV files, you can add waveform data to an existing map using the `addplot_waveform` method. This is particularly useful for acoustic monitoring, vibration analysis, and time-series anomaly detection.

**Important**: The `addplot_waveform` method automatically uses the same mkfftSeg preprocessing parameters (filters, window settings, etc.) as the basemap to ensure data consistency and accurate anomaly detection results.

```python
# Basic usage - add WAV file to the most recent map
result = client.addplot_waveform(["new_audio.wav"])

# Specify a target map number
result = client.addplot_waveform(["audio_data.wav"], mapNo=123)

# Process multiple files
wav_files = ["sample1.wav", "sample2.wav", "sample3.wav"]
result = client.addplot_waveform(wav_files)

# Mixed file types (WAV + CSV)
mixed_files = ["vibration.csv", "audio.wav"]
result = client.addplot_waveform(files=mixed_files)
```

#### Advanced Parameter Customization

```python
result = client.addplot_waveform(
    files=["machine_sound.wav"],
    mapNo=client.mapNo,  # Target map
    
    # identna parameters for custom normal area generation (optional)
    identna_resolution=100,      # Custom mesh resolution
    identna_effective_radius=0.1, # Custom effective radius
    
    # detabn parameters for abnormality detection
    detabn_max_window=3,         # Maximum window size
    detabn_rate_threshold=0.8,   # Abnormality rate threshold
    detabn_threshold=0.1,        # Normal area threshold
    detabn_print_score=True      # Include detailed scores
)

# Access comprehensive results
print(f"Add Plot Number: {result['addPlotNo']}")
print(f"Abnormality Status: {result['abnormalityStatus']}")  # 'normal', 'abnormal', 'unknown'
print(f"Abnormality Score: {result['abnormalityScore']}")
print(f"Coordinate Data Shape: {result['xyData'].shape}")
print(f"Share URL: {result['shareUrl']}")
```

### addplot_csvform()

For maps created with `fit_transform_csvform`, you can add CSV data using the `addplot_csvform` method. This method automatically uses the same CSV processing options (weight_option_str, type_option_str, drop_columns) that were used to create the base map, ensuring perfect consistency between the base map and additional plots.

```python
# Basic usage - add CSV file to a CSV-based map
result = client.addplot_csvform("new_data.csv")

# Specify a target map number
result = client.addplot_csvform("sensor_data.csv", mapNo=123)

# Process multiple CSV files
csv_files = ["batch1.csv", "batch2.csv", "batch3.csv"]
result = client.addplot_csvform(csv_files)

# With custom identna and abnormality detection parameters
result = client.addplot_csvform(
    "test_data.csv",
    identna_resolution=150,      # Custom mesh resolution for normal area
    identna_effective_radius=0.08, # Custom effective radius
    detabn_max_window=5,         # Maximum window size
    detabn_rate_threshold=0.8,   # Abnormality rate threshold
    detabn_threshold=0.1,        # Normal area threshold
    detabn_print_score=True      # Include detailed scores
)

# Access comprehensive results
print(f"Add Plot Number: {result['addPlotNo']}")
print(f"Abnormality Status: {result['abnormalityStatus']}")  # 'normal', 'abnormal', 'unknown'
print(f"Abnormality Score: {result['abnormalityScore']}")
print(f"Coordinate Data Shape: {result['xyData'].shape}")
print(f"Share URL: {result['shareUrl']}")
```

#### Key Features

- **Automatic Option Consistency**: The method retrieves and applies the same CSV processing options (weight_option_str, type_option_str, drop_columns) that were used when creating the base map
- **No Column Specification Needed**: Unlike general addplot methods, you don't need to specify weight or type options—they're automatically retrieved from the database
- **Dimension Validation**: The system automatically validates that the uploaded CSV has the same effective number of columns as the base map
- **Process Method Compatibility**: Only works with maps created using `fit_transform_csvform` (CSV-based maps)

---

## Map Management

### list_map()

Lists all available maps with their metadata.

```python
map_list = client.list_map()

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

### export_map()

Exports a map to a specified directory.

```python
map_no = client.mapNo  # Or any valid map number
client.export_map(map_no, "/path/to/export/directory")
```

**Important Note**: The export operation only includes base map files. Add plot files are excluded from the export. If your map includes add plots, you'll need to recreate them after importing the map.

### import_map()

Imports a map from a specified directory.

```python
new_map_no = client.import_map("/path/to/import/directory")
```

**Important Note**: The import operation only processes base map files. Any add plot files in the directory will be ignored. After importing a map, you must recreate any add plots using the `addplot` method.

**Function Aliases:**
- `import_map` can also be called as `upload_map`
- `export_map` can also be called as `download_map`

### Add Plot History

The client now maintains a history of all add plot operations for each map:

#### list_addplots()

Lists all add plots for a specific map.

```python
# List all add plots for a specific map
add_plots = client.list_addplots(client.mapNo)
print(f"Found {len(add_plots)} add plots for this map")

# Iterate through all add plots
if add_plots:
    for add_plot in add_plots:
        print(f"Add Plot #{add_plot['addPlotNo']} created at {add_plot['createdAt']}")
        print(f"Records: {add_plot['nRecord']}")
        print(f"Status: {add_plot.get('status', 'Unknown')}")  # Display normal/abnormal determination result
```

#### get_addplot()

Retrieves details about a specific add plot.

```python
# Get a specific add plot by its number
add_plot_info = client.get_addplot(client.mapNo, 1)  # Get the first add plot

# Access the add plot data
xy_data = add_plot_info['xyData']  # NumPy array of coordinates
add_plot_metadata = add_plot_info['addPlot']  # Metadata about the add plot
share_url = add_plot_info['shareUrl']  # Share URL for this specific add plot
```

#### get_addplot_features()

Provides detailed feature analysis of add plots (DataFrame and CSV-based maps only).

```python
# Get detailed feature analysis for a specific add plot
features = client.get_addplot_features(map_no=123, addplot_no=1)

# Convert to pandas DataFrame for easier analysis
df = client.to_dataframe(features)
```

**Important**: Feature analysis is only supported for DataFrame and CSV-based maps. This function is **not available for waveform-based maps** due to technical limitations.

---

## Parameter Details

### identna Parameters

Normal area identification parameters:

- **identna_resolution** (int, default=100): Mesh resolution for normal area identification. Higher values provide finer granularity but require more computation.
- **identna_effective_radius** (float, default=0.1): Effective radius as a ratio to the mesh area side length. Controls the influence radius around each data point.

### detabn Parameters

Abnormality detection parameters:

- **detabn_max_window** (int, default=5): Maximum number of sequential data points used for abnormality rate calculation
- **detabn_rate_threshold** (float, default=1.0): Lower threshold for abnormality rate (0.0 < rate <= 1.0). If rate >= threshold, data is considered abnormal
- **detabn_threshold** (int/float, default=0): Threshold for relative normal area value. If value > threshold, the point is considered normal
- **detabn_print_score** (bool, default=True): Whether to include detailed score information in the analysis

---

## Return Values

### Basic Method Returns

```python
# fit_transform methods return
{
    'mapNo': 123,
    'shareUrl': 'http://localhost:3000/map-inspector?...'
}

# addplot methods return
{
    'xyData': numpy.ndarray,        # 2D coordinate data
    'addPlotNo': 1,                 # Sequential add plot number
    'abnormalityStatus': 'normal',  # 'normal', 'abnormal', or 'unknown'
    'abnormalityScore': 0.25,       # Numerical abnormality score
    'shareUrl': 'http://...'        # Share URL for the updated map
}
```

### Client Properties

```python
# Access current state
print(client.mapNo)                # Most recent map number
print(client.shareUrl)             # Most recent share URL
print(client.currentAddPlotNo)     # Most recent add plot number
```

---

## Process Method Compatibility

toorPIA enforces strict compatibility between base map creation methods and addplot methods to ensure data consistency and accurate analysis results.

### Compatibility Matrix

| Base Map Method | addplot() | addplot_csvform() | addplot_waveform() |
|---|:---:|:---:|:---:|
| **fit_transform()** | ✅ | ❌ | ❌ |
| **fit_transform_csvform()** | ❌ | ✅ | ❌ |
| **fit_transform_waveform()** | ❌ | ❌ | ✅ |

### Supported Processing Methods

1. **DataFrame Processing** (`fit_transform` + `addplot`)
   - Base map: Created from pandas DataFrame or numpy arrays
   - Addplot: Uses processed data (columns, data arrays)
   - Use case: In-memory data processing with Python

2. **CSV Direct Processing** (`fit_transform_csvform` + `addplot_csvform`)
   - Base map: Created directly from CSV files
   - Addplot: Uses CSV files with automatically applied processing options
   - Use case: Large CSV files, consistent processing pipelines

3. **Waveform Processing** (`fit_transform_waveform` + `addplot_waveform`)
   - Base map: Created from WAV/CSV audio files
   - Addplot: Uses WAV/CSV files with FFT-based feature extraction
   - Use case: Audio analysis, vibration monitoring

### Compatibility Rules

**✅ Compatible Combinations:**
- DataFrame base map → `addplot()` method
- CSV base map → `addplot_csvform()` method
- Waveform base map → `addplot_waveform()` method

**❌ Incompatible Combinations:**
- DataFrame base map → `addplot_csvform()` or `addplot_waveform()`
- CSV base map → `addplot()` or `addplot_waveform()`
- Waveform base map → `addplot()` or `addplot_csvform()`

### Error Messages

When attempting incompatible combinations, you'll receive clear error messages:

```python
# Example: Using wrong addplot method
csv_base_map = client.fit_transform_csvform("baseline.csv")

# This will fail with a clear error
try:
    result = client.addplot(data_array)  # Wrong method for CSV base map
except Exception as e:
    print(e)  # "Cannot use DataFrame addplot with csvform basemap. Please use the matching addplot method."
```

---

## Advanced Features

### Checksum Calculation and Comparison

The client automatically calculates checksums for map data during import and export operations. This ensures data integrity and prevents unnecessary uploads of duplicate data.

**Note about checksums**: The checksum calculation now excludes add plot files and log files. Only base map files are considered when computing checksums. This ensures consistent checksums for the same base map, regardless of any add plot operations performed.

### Flexible Map Selection in addplot

The `addplot` method now supports flexible arguments:

- No additional argument: Uses the most recent map
- Integer argument: Uses the specified map number
- String argument: Uses the map data from the specified directory

```python
client.addplot(data)  # Uses most recent map
client.addplot(data, 123)  # Uses map number 123
client.addplot(data, "/path/to/map")  # Uses map data from the specified directory
```

---

## Share URL Feature

Each operation that modifies a map (fit_transform, addplot, etc.) generates a share URL that can be accessed through the `shareUrl` property of the client. This URL provides access to a graphical user interface where you can visually inspect and interact with the map data.

Example of accessing the share URL:
```python
# After creating or modifying a map
print(client.shareUrl)
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

---

## Performance Considerations

- Map exports may take some time, especially for large datasets.
- For `addplot` operations, consider performance implications when working with large map data directories.
- Data with more than 10,000 records may experience slower Map Inspector performance.

---

## Error Handling

The client provides informative error messages for various scenarios, including authentication failures, invalid requests, and server errors. Always check the return values and handle potential errors in your code.

```python
try:
    result = client.fit_transform(df)
    print(f"Success: {result['shareUrl']}")
except Exception as e:
    print(f"Error: {e}")
```

For more detailed information about specific methods and their parameters, refer to the inline documentation in the source code.

---

## Next Steps

- [Map Inspector Guide](map-inspector.md) - Learn how to use the visual analysis interface
- [Troubleshooting](troubleshooting.md) - Common issues and solutions