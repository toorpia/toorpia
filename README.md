# toorPIA API Client

This is a Python library for generating toorPIA maps from CSV and audio data, enabling visual data analysis.

---

## Quick Start

### Try the Interactive Notebook First (Recommended)

For hands-on experience, run the interactive Jupyter notebook:

**Google Colab (recommended):**  
[Open in Google Colab](https://colab.research.google.com/github/toorpia/toorpia/blob/main/samples/test_toorpia_api.ipynb)

**Local Jupyter:**
```bash
jupyter notebook samples/test_toorpia_api.ipynb
```

### API Key Setup

To get your API key:
1. Log in to https://api.toorpia.com/ with your account credentials provided by toor
2. Generate an API Key in the dashboard

Then configure the API key in your environment:

**For Google Colab (recommended):**
1. Click the 🔑 (key icon) in the left panel
2. Click "New secret" 
3. Name: `TOORPIA_API_KEY`, Value: your actual API key
4. Save

**For local environment:**
```bash
export TOORPIA_API_KEY='your-api-key'
```

---

## Installation

For local development and production use, install toorPIA in your Python environment:

```bash
pip install git+https://github.com/toorpia/toorpia.git
```

### Core Workflow: Basemap → Addplot Analysis

toorPIA follows a simple two-step workflow for data analysis and anomaly detection:

1. **Create Base Map**: Establish normal data patterns using `basemap_*()` methods
2. **Add New Data**: Test new data for anomalies using `addplot_*()` methods

## CSV Data Analysis

### Step 1: Create Base Map from CSV

```python
from toorpia import toorPIA

# Initialize client
client = toorPIA()

# Create base map from CSV file
result = client.basemap_csvform(
    "samples/biopsy.csv",
    weight_option_str="1:0,2:0,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0",
    type_option_str="1:int,2:none,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,12:enum",
    # drop_columns=["No", "ID"],  # Alternative: automatic column exclusion
    label="Breast Cancer Biopsy Analysis",
    tag="Medical Diagnostics",
    identna_resolution=200,
    identna_effective_radius=0.2
)

print(f"✅ Base map created!")
print(f"Map Number: {result['mapNo']}")
print(f"Coordinates Shape: {result['xyData'].shape}")  
print(f"🌐 View Map: {result['shareUrl']}")
```

**Tip:** For simpler column exclusion, use `drop_columns=["No", "ID"]` instead of manual weight/type specifications. Note that `drop_columns` takes precedence over `weight_option_str`/`type_option_str`.

### Step 2: Add New Data for Anomaly Detection

```python
# Test new data against the latest base map
addplot_result = client.addplot_csvform("new_data.csv")

# Or specify a previous basemap by map number
addplot_result = client.addplot_csvform("new_data.csv", mapNo=123)

print(f"Abnormality Status: {addplot_result['abnormalityStatus']}")
if addplot_result['abnormalityStatus'] == 'abnormal':
    print(f"🚨 Anomaly detected! Score: {addplot_result['abnormalityScore']:.3f}")
else:
    print(f"✅ Data is normal")

print(f"🌐 View Results: {addplot_result['shareUrl']}")
```

## Audio & Acoustic Analysis

### Step 1: Create Base Map from Audio Files  

```python
# Create base map from multiple WAV files
result = client.basemap_waveform(
    ["machine1.wav", "machine2.wav", "machine3.wav"],
    mkfftseg_hp=1000.0,     # High-pass filter at 1kHz
    mkfftseg_lp=8000.0,     # Low-pass filter at 8kHz  
    mkfftseg_wl=4096,       # FFT window length
    mkfftseg_wf="hamming",  # Window function
    label="Machine Sound Baseline",
    tag="Acoustic Monitoring",
    identna_resolution=150
)

print(f"✅ Audio base map created!")
print(f"Map Number: {result['mapNo']}")
print(f"🌐 View Spectral Map: {result['shareUrl']}")
```

### Step 2: Detect Audio Anomalies

```python
# Test suspicious audio against the latest basemap
test_result = client.addplot_waveform(["suspicious_sound.wav"])

# Or test against a specific previous basemap
test_result = client.addplot_waveform(["suspicious_sound.wav"], mapNo=456)

if test_result['abnormalityStatus'] == 'abnormal':
    print(f"🚨 Acoustic anomaly detected!")
    print(f"Abnormality Score: {test_result['abnormalityScore']:.3f}")
    print(f"This sound pattern deviates from normal baseline")
else:
    print(f"✅ Audio pattern is normal")

print(f"🌐 View Analysis: {test_result['shareUrl']}")
```

## Visual Analysis with Map Inspector

All basemap and addplot operations generate interactive visualizations accessible through share URLs.

**Map Inspector Features:**
- **Green point clouds**: Normal baseline data distribution  
- **Red × marks**: Anomalous data points (when detected)
- **Concentric grid patterns**: Normal regions and boundaries
- **Interactive controls**: Zoom, filter, region selection
- **Statistical analysis**: Data distribution metrics

## API Reference

### Unified Return Value Structure

All `basemap_*()` and `addplot_*()` methods return consistent dictionary structures:

#### `basemap_csvform()` and `basemap_waveform()` Return Values

```python
result = client.basemap_csvform("data.csv")
# or
result = client.basemap_waveform(["audio1.wav", "audio2.wav"])

# Returns: Dictionary with structured metadata
{
    'xyData': numpy.ndarray,     # Coordinate data (n_samples, 2)
    'mapNo': 12345,              # Map identification number  
    'shareUrl': 'http://...'     # Interactive visualization URL
}

# Client instance attributes are also automatically updated:
print(f"Current map: {client.mapNo}")     # Same as result['mapNo']
print(f"View online: {client.shareUrl}")  # Same as result['shareUrl']
```

#### `addplot_csvform()` and `addplot_waveform()` Return Values

```python
result = client.addplot_csvform("new_data.csv")
# or 
result = client.addplot_waveform(["new_audio.wav"])

# Returns: Dictionary with anomaly detection results
{
    'xyData': numpy.ndarray,           # Coordinate data (n_samples, 2)
    'addPlotNo': 1,                    # Sequential addplot number
    'abnormalityStatus': 'abnormal',   # 'normal', 'abnormal', 'unknown'
    'abnormalityScore': 2.47,          # Numerical anomaly score
    'shareUrl': 'http://...'           # Updated visualization URL
}
```

**Working with Coordinate Data:**
```python
# Extract coordinate data for plotting
coords = result['xyData']
x_coords = coords[:,0] 
y_coords = coords[:,1]

# Create custom visualization
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 8))
plt.scatter(x_coords, y_coords, alpha=0.6)
plt.title("Data Distribution Map")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.show()

# Check anomaly detection results (for addplot methods)
if 'abnormalityStatus' in result:
    if result['abnormalityStatus'] == 'abnormal':
        print(f"⚠️  Anomaly detected! Score: {result['abnormalityScore']}")
    else:
        print(f"✅ Data is within normal patterns")
    
# View interactive results online
print(f"🌐 Explore data: {result['shareUrl']}")
```

---

## Advanced Features

### Alternative: DataFrame-based Processing

Similar to scikit-learn's PCA or t-SNE, you can use `fit_transform()` for direct DataFrame processing:

```python  
import pandas as pd

# Load data into DataFrame
df = pd.read_csv("data.csv")
df_clean = df.drop(columns=['ID', 'Timestamp'])  # Pandas-based column removal

# Create base map from DataFrame (returns coordinate array)
coords = client.fit_transform(
    df_clean,
    label="DataFrame-based Processing",
    identna_resolution=150
)

print(f"Coordinate data shape: {coords.shape}")  # (n_samples, 2)

# Client instance attributes are automatically updated:
print(f"Map Number: {client.mapNo}")
print(f"Share URL: {client.shareUrl}")

# Add new data for anomaly detection
df_new = pd.read_csv("new_data.csv").drop(columns=['ID', 'Timestamp'])
addplot_result = client.addplot(df_new)
print(f"Anomaly status: {addplot_result['abnormalityStatus']}")
```

**Key Differences:**
- `fit_transform()`: Returns `numpy.ndarray` (coordinate data only)
- `basemap_*()`: Returns `dict` with structured metadata (`xyData`, `mapNo`, `shareUrl`)
- **Both approaches**: Automatically update `client.mapNo` and `client.shareUrl` attributes

---

## Documentation

- **[API Reference](docs/api-reference.md)** - Detailed specifications for all methods and parameters
- **[Map Inspector Guide](docs/map-inspector.md)** - Visual analysis tool usage
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

---

## Key Features

### Data Processing Methods
- **DataFrame Processing**: Direct processing of pandas/numpy data
- **CSV Direct Processing**: Memory-efficient processing of large files
- **Audio Processing**: FFT feature extraction from WAV/CSV files

### Anomaly Detection
- Learning normal data patterns
- Automatic anomaly judgment for new data
- Visual identification of anomalous locations

### Map Inspector (GUI)
- Interactive data visualization
- Attribute-based color coding
- Region selection and statistical analysis
- Heatmap display
- Sub-map generation and data cleansing

---

## Environment Configuration

### API Configuration

```bash
# API Key
export TOORPIA_API_KEY='your-api-key'

# On-premise environment
export TOORPIA_API_URL='http://your-server:3000'
```

### MCP Server for Claude Desktop

> ⚠️ **Work In Progress** - This feature is currently under development and may not work as expected.

Integration with Claude Desktop enables natural language toorPIA operations:

```bash
cd mcp && npm install && npm run build
```

For details, see [mcp/README.md](./mcp/README.md).

