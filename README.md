# toorPIA API Client

toorPIA is a Python library for generating anomaly detection maps from CSV and audio data, enabling visual data analysis.

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

### Basic Usage

Let's explore toorPIA's core features using sample data.

```python
from toorpia import toorPIA
import pandas as pd

# Create API client
client = toorPIA()

# Load sample data
df = pd.read_csv("samples/biopsy.csv")

# Examine data structure
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(df.head(3))
```

**Output example:**
```
Data shape: (683, 11)
Columns: ['No', 'ID', 'Clump Thickness', 'Uniformity of Cell Size', ...]
   No        ID  Clump Thickness  Uniformity of Cell Size  ...
0   1   1000025                5                        1  ...
1   2   1002945                5                        4  ...
2   3   1015425                3                        1  ...
```

### Creating a Base Map

Remove management columns and create a base map for analysis.

```python
# Prepare analysis DataFrame by excluding management columns
analysis_df = df.drop(columns=['No', 'ID', 'Diagnosis'])

# Create base map (execution time: ~5 seconds)
result = client.fit_transform(
    analysis_df,
    label="Breast Cancer Biopsy Data",
    tag="Medical Analysis",
    description="Wisconsin Breast Cancer diagnostic features"
)

print(f"Map Number: {client.mapNo}")
print(f"Map Inspector URL: {client.shareUrl}")
```

### Visual Analysis

The generated map can be analyzed visually in your browser.

```python
# Open Map Inspector in browser for visualization
print(f"🌐 View base map: {client.shareUrl}")
```

Map Inspector provides:
- Green point clouds showing normal data distribution
- Concentric grid patterns representing normal regions
- Interactive data exploration capabilities

### Adding New Data and Anomaly Detection

```python
# Load additional data
df_add = pd.read_csv("samples/biopsy-add.csv")

# Remove management columns consistently
analysis_add = df_add.drop(columns=['No', 'ID', 'Diagnosis'])

# Perform anomaly detection
result_add = client.addplot(analysis_add)

# Check results
print(f"🚨 Anomaly detection results: {client.shareUrl}")
print(f"Abnormality Status: {result_add['abnormalityStatus']}")
print(f"Abnormality Score: {result_add['abnormalityScore']:.3f}")
```

Anomalous data points are visually indicated by red × marks in Map Inspector.

### Return Value Structure

#### `fit_transform()` Return Value

**Data Structure:**
```python
result = client.fit_transform(df)
# Returns: numpy array with shape (n_samples, 2)
# [[x1, y1],
#  [x2, y2], 
#  [x3, y3],
#  ...]
```

**How to Use:**
```python
# Get X coordinates (all rows, column 0)
x_coords = result[:,0]

# Get Y coordinates (all rows, column 1) 
y_coords = result[:,1]

# Plot the results
import matplotlib.pyplot as plt
plt.scatter(x_coords, y_coords)
# Or simply: plt.scatter(result[:,0], result[:,1])
```

**Client attributes automatically set:**
- `client.mapNo` - Map ID number for future reference
- `client.shareUrl` - Clickable URL to view results online

#### `addplot()` Return Value

**Data Structure:**
```python
result = client.addplot(new_data)
# Returns: Dictionary with multiple pieces of information
{
    'xyData': numpy.ndarray,        # Same structure as fit_transform result
    'addPlotNo': 1,                 # Sequential number for this addition
    'abnormalityStatus': 'normal',  # 'normal', 'abnormal', or 'unknown'
    'abnormalityScore': 0.25,       # Numerical anomaly score
    'shareUrl': 'http://...'        # Updated URL including this addition
}
```

**How to Use:**
```python
# Extract coordinate data for plotting
coords = result['xyData']
x_coords = coords[:,0] 
y_coords = coords[:,1]

# Check anomaly detection results
if result['abnormalityStatus'] == 'abnormal':
    print(f"⚠️  Anomaly detected! Score: {result['abnormalityScore']}")
    
# View results online
print(f"🌐 View results: {result['shareUrl']}")
```

---

## Advanced Usage

### Direct Processing of Large CSV Files

Memory-efficient direct processing of CSV files:

```python
# Direct CSV processing (memory efficient)
result = client.fit_transform_csvform(
    "large_dataset.csv",
    drop_columns=["ID", "Timestamp"],  # Exclude unnecessary columns
    identna_resolution=200,            # High resolution
    label="Production Line Data"
)
```

### Audio and Vibration Data Analysis

Feature extraction from WAV files or CSV time-series data:

```python
# Audio data analysis
result = client.fit_transform_waveform(
    files=["machine_sound.wav"],
    mkfftseg_hp=100.0,        # High-pass filter at 100Hz
    mkfftseg_lp=8000.0,       # Low-pass filter at 8kHz
    label="Machine Audio Analysis"
)

# Anomalous sound detection
test_result = client.addplot_waveform(
    files=["suspicious_sound.wav"]
)
```

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

