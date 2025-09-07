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

#### 2. Creating a Base Map from CSV Files (Direct Processing)

```python
# Basic single CSV file processing
result = toorpia_client.fit_transform_csvform("sensor_data.csv")
print(f"Map Number: {toorpia_client.mapNo}")
print(f"Share URL: {toorpia_client.shareUrl}")

# Multiple CSV files processing (automatically merged)
csv_files = ["data1.csv", "data2.csv", "data3.csv"]
result = toorpia_client.fit_transform_csvform(csv_files)

# Using drop_columns to exclude specific columns
result = toorpia_client.fit_transform_csvform(
    "data.csv",
    drop_columns=["ID", "Timestamp", "Comments"]  # These columns will be excluded
)

# Fine control with weight and type options
result = toorpia_client.fit_transform_csvform(
    "sensor_data.csv",
    weight_option_str="1:0,2:0,3:1,4:1,5:1",  # Columns 1,2 have weight 0
    type_option_str="1:none,2:none,3:float,4:float,5:int"
)

# Complete example with all parameters
result = toorpia_client.fit_transform_csvform(
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

##### Parameters for CSV Direct Processing

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

#### 3. Creating a Base Map from WAV (Sound) Data

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

#### 4. Adding Data to an Existing Map

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

##### Advanced: Custom identna Parameters for Normal Area Generation

You can override the base map's identna parameters for custom normal area generation when adding data:

```python
result = toorpia_client.addplot(
    df_add,
    identna_resolution=50,          # Custom mesh resolution (default: inherit from basemap)
    identna_effective_radius=0.05   # Custom effective radius (default: inherit from basemap)
)

# When identna parameters are provided:
# - A custom normal area file is generated using these parameters
# - The AddPlot record shows source='custom' for parameter tracking
# - If not provided, parameters are inherited from the basemap with source='basemap'
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

#### 4.1. Adding WAV/CSV Data to an Existing Map (Waveform Addplot)

For WAV and CSV files, you can add waveform data to an existing map using the `addplot_waveform` method. This is particularly useful for acoustic monitoring, vibration analysis, and time-series anomaly detection.

**Important**: The `addplot_waveform` method automatically uses the same mkfftSeg preprocessing parameters (filters, window settings, etc.) as the basemap to ensure data consistency and accurate anomaly detection results.

```python
# Basic usage - add WAV file to the most recent map
result = toorpia_client.addplot_waveform(["new_audio.wav"])

# Specify a target map number
result = toorpia_client.addplot_waveform(["audio_data.wav"], mapNo=123)

# Process multiple files
wav_files = ["sample1.wav", "sample2.wav", "sample3.wav"]
result = toorpia_client.addplot_waveform(wav_files)

# Mixed file types (WAV + CSV)
mixed_files = ["vibration.csv", "audio.wav"]
result = toorpia_client.addplot_waveform(files=mixed_files)
```

##### Advanced Parameter Customization

```python
result = toorpia_client.addplot_waveform(
    files=["machine_sound.wav"],
    mapNo=toorpia_client.mapNo,  # Target map
    
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

##### Practical Use Cases

**Acoustic Monitoring Example:**
```python
# Create baseline from normal operation sounds
baseline_files = ["normal_operation_1.wav", "normal_operation_2.wav"]
baseline_result = toorpia_client.fit_transform_waveform(
    files=baseline_files,
    mkfftseg_hp=100.0,  # Configure preprocessing for baseline
    mkfftseg_lp=8000.0, # These settings will be used for all addplots
    label="Machine Baseline - Normal Operation",
    tag="Acoustic Monitoring"
)

# Add potentially abnormal sound for comparison
# Note: mkfftSeg parameters are automatically inherited from baseline
test_result = toorpia_client.addplot_waveform(
    files=["suspicious_sound.wav"],
    detabn_rate_threshold=0.7  # Sensitive abnormality detection
)

if test_result['abnormalityStatus'] == 'abnormal':
    print("⚠️  Abnormal sound detected!")
    print(f"Abnormality score: {test_result['abnormalityScore']}")
```

**Vibration Analysis Example:**
```python
# Create baseline with appropriate CSV settings
baseline_result = toorpia_client.fit_transform_waveform(
    files=["baseline_vibration.csv"],
    mkfftseg_di=3,      # Use 3rd column (acceleration data)
    mkfftseg_sr=1000,   # 1kHz sampling rate
    mkfftseg_wl=2048,   # Shorter window for vibration analysis
    label="Vibration Baseline"
)

# Analyze new vibration data with consistent preprocessing
vibration_result = toorpia_client.addplot_waveform(
    files=["vibration_sensor.csv"],
    detabn_max_window=5 # Analyze 5-point sequences
)
# mkfftSeg settings (di=3, sr=1000, wl=2048) are automatically applied
```

##### Return Value Details

The `addplot_waveform` method returns a dictionary with the following keys:

- **`xyData`**: NumPy array of 2D coordinates representing the processed waveform data
- **`addPlotNo`**: Sequential number of this add plot within the target map
- **`abnormalityStatus`**: Abnormality detection result ('normal', 'abnormal', or 'unknown')
- **`abnormalityScore`**: Numerical abnormality score (lower values indicate more normal behavior)
- **`shareUrl`**: Updated share URL including this add plot for Map Inspector visualization

##### Parameter Reference

**Preprocessing Consistency**: mkfftSeg parameters (filters, window settings, etc.) are automatically inherited from the basemap to ensure data consistency. These cannot be customized in addplot operations.

**identna Parameters** (optional - for custom normal area generation):
- `identna_resolution` (int): Custom mesh resolution for normal area generation
- `identna_effective_radius` (float): Custom effective radius for normal area generation

**detabn Parameters** (for abnormality detection):
- `detabn_max_window` (int): Maximum window size for abnormality detection
- `detabn_rate_threshold` (float): Rate threshold for abnormality detection  
- `detabn_threshold` (int): Threshold value for abnormality detection
- `detabn_print_score` (bool): Whether to print abnormality score details

**File Support**: 
- WAV files: Automatic sample rate detection
- CSV files: Sample rate and column settings inherited from basemap
- Mixed processing: Both file types in a single operation

#### 4.2. Adding CSV Data to CSV-based Maps (CSV Addplot)

For maps created with `fit_transform_csvform`, you can add CSV data using the `addplot_csvform` method. This method automatically uses the same CSV processing options (weight_option_str, type_option_str, drop_columns) that were used to create the base map, ensuring perfect consistency between the base map and additional plots.

```python
# Basic usage - add CSV file to a CSV-based map
result = toorpia_client.addplot_csvform("new_data.csv")

# Specify a target map number
result = toorpia_client.addplot_csvform("sensor_data.csv", mapNo=123)

# Process multiple CSV files
csv_files = ["batch1.csv", "batch2.csv", "batch3.csv"]
result = toorpia_client.addplot_csvform(csv_files)

# With custom identna and abnormality detection parameters
result = toorpia_client.addplot_csvform(
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

##### Key Features

- **Automatic Option Consistency**: The method retrieves and applies the same CSV processing options (weight_option_str, type_option_str, drop_columns) that were used when creating the base map
- **No Column Specification Needed**: Unlike general addplot methods, you don't need to specify weight or type options—they're automatically retrieved from the database
- **Dimension Validation**: The system automatically validates that the uploaded CSV has the same effective number of columns as the base map
- **Process Method Compatibility**: Only works with maps created using `fit_transform_csvform` (CSV-based maps)

##### Practical Example

```python
# Step 1: Create a base map with specific CSV options
base_result = toorpia_client.fit_transform_csvform(
    "production_baseline.csv",
    drop_columns=["ID", "Timestamp"],  # Exclude these columns
    weight_option_str="3:1,4:1,5:0.5,6:1,7:1",  # Custom weights
    identna_resolution=200,
    label="Production Baseline"
)

# Step 2: Add new data using the same processing options automatically
test_result = toorpia_client.addplot_csvform(
    "daily_production.csv",  # Same structure as baseline
    detabn_rate_threshold=0.7  # Sensitive abnormality detection
)

# The system automatically:
# - Applies the same drop_columns=["ID", "Timestamp"]
# - Uses the same weight_option_str="3:1,4:1,5:0.5,6:1,7:1"
# - Validates column count consistency
# - Performs abnormality detection against the baseline

if test_result['abnormalityStatus'] == 'abnormal':
    print("⚠️ Production anomaly detected!")
    print(f"Abnormality score: {test_result['abnormalityScore']}")
```

##### Error Handling

The method includes comprehensive error checking:

- **Process Method Compatibility**: Throws an error if used with non-CSV-based maps
- **Column Count Validation**: Verifies that the CSV has the correct number of effective columns
- **File Format Validation**: Ensures only CSV files are uploaded

##### Return Value

Returns a dictionary with the same structure as other addplot methods:
- **`xyData`**: NumPy array of 2D coordinates
- **`addPlotNo`**: Sequential add plot number
- **`abnormalityStatus`**: 'normal', 'abnormal', or 'unknown'
- **`abnormalityScore`**: Numerical abnormality score
- **`shareUrl`**: Updated share URL including this add plot

#### 4.3. Working with Add Plot History

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

### Process Method Compatibility

toorPIA enforces strict compatibility between base map creation methods and addplot methods to ensure data consistency and accurate analysis results.

#### Supported Processing Methods

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

#### Compatibility Rules

**✅ Compatible Combinations:**
- DataFrame base map → `addplot()` method
- CSV base map → `addplot_csvform()` method
- Waveform base map → `addplot_waveform()` method

**❌ Incompatible Combinations:**
- DataFrame base map → `addplot_csvform()` or `addplot_waveform()`
- CSV base map → `addplot()` or `addplot_waveform()`
- Waveform base map → `addplot()` or `addplot_csvform()`

#### Error Messages

When attempting incompatible combinations, you'll receive clear error messages:

```python
# Example: Using wrong addplot method
csv_base_map = toorpia_client.fit_transform_csvform("baseline.csv")

# This will fail with a clear error
try:
    result = toorpia_client.addplot(data_array)  # Wrong method for CSV base map
except Exception as e:
    print(e)  # "Cannot use DataFrame addplot with csvform basemap. Please use the matching addplot method."
```

#### Technical Implementation

The system tracks the processing method used for each base map and validates compatibility:

- **processMethod field**: Automatically set during base map creation ('dataframe', 'csvform', 'waveform')
- **Automatic validation**: Each addplot method checks compatibility before processing
- **Clear guidance**: Error messages specify the correct method to use

This strict separation ensures:
- **Data Consistency**: Processing options remain consistent between base map and addplots
- **Analysis Accuracy**: No mixing of different data processing paradigms
- **User Guidance**: Clear error messages prevent confusion

#### 5. Listing Available Maps

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

#### 6. Exporting a Map

```python
map_no = toorpia_client.mapNo  # Or any valid map number
toorpia_client.export_map(map_no, "/path/to/export/directory")
```

**Important Note**: The export operation only includes base map files. Add plot files are excluded from the export. If your map includes add plots, you'll need to recreate them after importing the map.

#### 7. Importing a Map

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

#### Feature Analysis

The client provides the `get_addplot_features()` method for detailed feature analysis of add plots:

```python
# Get detailed feature analysis for a specific add plot
features = toorpia_client.get_addplot_features(map_no=123, addplot_no=1)

# Convert to pandas DataFrame for easier analysis
df = toorpia_client.to_dataframe(features)
```

**Important**: Feature analysis is only supported for DataFrame and CSV-based maps. This function is **not available for waveform-based maps** due to technical limitations.

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

## Integrations

### MCP Server for Claude Desktop

toorPIA provides a Model Context Protocol (MCP) server that enables seamless integration with Claude Desktop. Execute all toorPIA operations through natural language conversations without writing Python code.

#### Key Benefits
- **Natural Language Interface**: Perform complex data analysis through conversational AI
- **Complete Functionality**: Access all 11 toorPIA tools directly from Claude Desktop
- **No Programming Required**: Perfect for non-technical users and rapid prototyping

#### Quick Setup

1. **Build the MCP server:**
   ```bash
   cd mcp && npm install && npm run build
   ```

2. **Configure environment:**
   ```bash
   export TOORPIA_API_KEY="your-api-key"
   ```

3. **Add to Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "toorpia": {
         "command": "node",
         "args": ["./path/to/toorpia/mcp/dist/index.js"],
         "env": {
           "TOORPIA_API_KEY": "your-api-key"
         }
       }
     }
   }
   ```

#### Usage Examples

**Create a basemap:**
> "Create a base map from `/data/sensor_readings.csv` labeled 'Production Line A'"

**Analyze audio for anomalies:**
> "Add the audio file `/sounds/machine_today.wav` to the current map and check for abnormal patterns"

**For detailed setup, configuration, and all available tools:** See [mcp/README.md](./mcp/README.md)
