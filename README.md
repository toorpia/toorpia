# toorPIA API Client

toorPIA is a Python library for generating anomaly detection maps from CSV and audio data, enabling visual data analysis.

## Installation

```bash
pip install git+https://github.com/toorpia/toorpia.git
```

## Quick Start

### Environment Setup

```bash
export TOORPIA_API_KEY='your-api-key'
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

```python
# fit_transform return value
{
    'mapNo': 123,              # Map number
    'shareUrl': 'http://...'   # Map Inspector URL
}

# addplot return value
{
    'xyData': numpy.ndarray,        # 2D coordinate data
    'addPlotNo': 1,                 # Add plot number
    'abnormalityStatus': 'normal',  # 'normal', 'abnormal', 'unknown'
    'abnormalityScore': 0.25,       # Anomaly score (numeric)
    'shareUrl': 'http://...'        # Map Inspector URL
}
```

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

## Documentation

- **[API Reference](docs/api-reference.md)** - Detailed specifications for all methods and parameters
- **[Map Inspector Guide](docs/map-inspector.md)** - Visual analysis tool usage
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

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

## Environment Configuration

### API Configuration

```bash
# API Key
export TOORPIA_API_KEY='your-api-key'

# On-premise environment
export TOORPIA_API_URL='http://your-server:3000'
```

### MCP Server for Claude Desktop

Integration with Claude Desktop enables natural language toorPIA operations:

```bash
cd mcp && npm install && npm run build
```

For details, see [mcp/README.md](./mcp/README.md).

## Samples and Learning Resources

- `samples/biopsy.csv` - Medical diagnostic data sample
- `samples/biopsy-add.csv` - Sample for additional plotting

## Support

- GitHub Issues: Bug reports and feature requests
- Documentation: Latest usage and best practices

---

**Next Steps**: Check the [API Reference](docs/api-reference.md) for detailed customization methods.