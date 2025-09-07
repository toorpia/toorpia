# toorPIA Troubleshooting

This document explains potential issues that may occur when using toorPIA and their solutions.

## Table of Contents

- [Installation and Environment Setup](#installation-and-environment-setup)
- [Authentication and Connection Errors](#authentication-and-connection-errors)
- [Data Processing Errors](#data-processing-errors)
- [Map Inspector Issues](#map-inspector-issues)
- [Performance Issues](#performance-issues)
- [API Call Errors](#api-call-errors)
- [Frequently Asked Questions](#frequently-asked-questions)

---

## Installation and Environment Setup

### pip install Fails

**Symptoms**: Error occurs with `pip install git+https://github.com/toorpia/toorpia.git`

**Causes and Solutions**:

1. **Insufficient Git Access Permissions**
   ```bash
   # Try accessing via HTTPS
   pip install git+https://github.com/toorpia/toorpia.git
   
   # If SSH keys are configured
   pip install git+ssh://git@github.com/toorpia/toorpia.git
   ```

2. **Python Environment Issues**
   ```bash
   # Create virtual environment
   python -m venv toorpia-env
   source toorpia-env/bin/activate  # Linux/Mac
   # or
   toorpia-env\Scripts\activate  # Windows
   
   # Then install
   pip install git+https://github.com/toorpia/toorpia.git
   ```

3. **Dependency Conflicts**
   ```bash
   pip install --upgrade pip
   pip install git+https://github.com/toorpia/toorpia.git --force-reinstall
   ```

### Environment Variables Not Recognized

**Symptoms**: API key error occurs despite setting `TOORPIA_API_KEY`

**Solutions**:

```python
import os

# 1. Check environment variables
print("API Key:", os.environ.get('TOORPIA_API_KEY'))

# 2. Set directly in program
os.environ['TOORPIA_API_KEY'] = 'your-api-key'

# 3. Specify explicitly when creating client
from toorpia import toorPIA
client = toorPIA(api_key='your-api-key')
```

**Persistent Setup**:

```bash
# Linux/Mac (add to .bashrc or .zshrc)
export TOORPIA_API_KEY='your-api-key'
export TOORPIA_API_URL='http://your-server:3000'  # On-premise environment

# Windows (Command Prompt)
setx TOORPIA_API_KEY "your-api-key"

# Windows (PowerShell)
$env:TOORPIA_API_KEY = "your-api-key"
```

---

## Authentication and Connection Errors

### API Authentication Error

**Symptoms**: `Authentication failed` or `Invalid API key` errors

**Resolution Steps**:

1. **Check API Key**
   ```python
   from toorpia import toorPIA
   client = toorPIA()
   
   # Check API key status
   try:
       maps = client.list_map()
       print("✅ API authentication successful")
   except Exception as e:
       print(f"❌ Authentication error: {e}")
   ```

2. **Check Key Format**
   - Ensure no extra spaces or newline characters in API key
   - Ensure no quote characters are included

3. **Check Permissions**
   - API key validity period
   - Access permission scope

### Connection Timeout

**Symptoms**: `Connection timeout` or `Request timeout` errors

**Solutions**:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Adjust timeout settings
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Extend timeout for large file processing
client = toorPIA(timeout=300)  # Extend to 5 minutes
```

### On-Premise Environment Connection Issues

**Symptoms**: Cannot connect to on-premise server

**Checkpoints**:

1. **URL Configuration Check**
   ```bash
   # Correct protocol and port
   export TOORPIA_API_URL='http://192.168.1.100:3000'
   # or
   export TOORPIA_API_URL='https://toorpia.company.com'
   ```

2. **Firewall Settings**
   - Check if specified port is open
   - Verify proxy settings are correct

3. **SSL Certificate Issues (HTTPS Environment)**
   ```python
   # Solutions for self-signed certificates
   import requests
   requests.packages.urllib3.disable_warnings()
   
   # Or set via environment variable
   os.environ['REQUESTS_CA_BUNDLE'] = ''
   ```

---

## Data Processing Errors

### CSV File Reading Error

**Symptoms**: `File not found` or `CSV parsing error`

**Solutions**:

1. **Check File Path**
   ```python
   import os
   
   # Check file existence
   file_path = "data/sample.csv"
   if os.path.exists(file_path):
       print(f"✅ File confirmed: {file_path}")
   else:
       print(f"❌ File not found: {file_path}")
       
   # Use absolute path
   abs_path = os.path.abspath(file_path)
   result = client.fit_transform_csvform(abs_path)
   ```

2. **CSV Format Issues**
   ```python
   import pandas as pd
   
   # Check CSV beforehand
   try:
       df = pd.read_csv("data.csv")
       print(f"✅ CSV reading successful: {df.shape}")
       print(f"Column names: {df.columns.tolist()}")
   except Exception as e:
       print(f"❌ CSV reading error: {e}")
   ```

3. **Encoding Issues**
   ```python
   # For Japanese data
   df = pd.read_csv("data.csv", encoding='utf-8')
   # or
   df = pd.read_csv("data.csv", encoding='shift_jis')
   ```

### Data Type Error

**Symptoms**: `Invalid data type` or `Column type mismatch`

**Solutions**:

```python
import pandas as pd

# Check and fix data types
df = pd.read_csv("data.csv")
print("Data types:")
print(df.dtypes)

# Convert numeric columns
df['numeric_column'] = pd.to_numeric(df['numeric_column'], errors='coerce')

# Check for invalid values
print("Missing values:")
print(df.isnull().sum())

# Remove invalid values
df_clean = df.dropna()

# Process with toorPIA
result = client.fit_transform(df_clean)
```

### Dimension Mismatch Error

**Symptoms**: `Dimension mismatch` or `Column count error`

**Solutions for addplot**:

```python
# Check base map information
map_info = client.list_map()
print(f"Base map column count check required")

# Check additional data column count
print(f"Additional data column count: {additional_data.shape[1]}")

# Adjust column count
if additional_data.shape[1] != expected_columns:
    print("Please adjust column count")
    # Remove unnecessary columns
    additional_data = additional_data.drop(['unnecessary_column'], axis=1)
```

---

## Map Inspector Issues

### Map Inspector Won't Start

**Symptoms**: Page doesn't display when accessing `shareUrl`

**Solutions**:

1. **URL Format Check**
   ```python
   print(f"Share URL: {client.shareUrl}")
   # Normal format: http://localhost:3000/map-inspector?seg=...&segHash=...
   ```

2. **Server Status Check**
   - Check if toorPIA server is running
   - Check if port 3000 is accessible

3. **Browser Cache Clearing**
   - Clear browser cache and cookies
   - Try incognito/private browsing mode

### Map Inspector Runs Slowly

**Symptoms**: Map display and operations take a long time

**Optimization Methods**:

1. **Reduce Data Size**
   ```python
   # Reduce data through sampling
   df_sample = df.sample(n=5000, random_state=42)
   result = client.fit_transform(df_sample)
   ```

2. **Browser Optimization**
   - Close unnecessary browser tabs
   - Temporarily disable browser extensions
   - Use latest versions of Chrome or Firefox

3. **System Resource Check**
   - Check memory usage
   - Monitor CPU usage

### State Save Fails

**Symptoms**: "Status file save failed" error

**Causes and Solutions**:

1. **Conflicts Between Multiple Map Inspectors**
   ```python
   # Use different state files
   params_1 = {'status_mi': 'analysis/status-1.mi'}
   params_2 = {'status_mi': 'analysis/status-2.mi'}
   ```

2. **File Permission Issues**
   ```bash
   # Check working directory permissions
   ls -la working_directory/
   
   # Fix permissions (if necessary)
   chmod 755 working_directory/
   ```

---

## Performance Issues

### Long Processing Time

**Symptoms**: `fit_transform` or `addplot` takes abnormally long

**Optimization Methods**:

1. **Data Size Optimization**
   ```python
   # Check data size
   print(f"Data size: {df.shape}")
   
   # Consider sampling for over 10,000 rows
   if df.shape[0] > 10000:
       df_sample = df.sample(n=8000, random_state=42)
       print(f"After sampling: {df_sample.shape}")
   ```

2. **Reduce Column Count**
   ```python
   # Remove unnecessary columns
   unnecessary_cols = ['id', 'timestamp', 'notes']
   df_optimized = df.drop(columns=unnecessary_cols)
   ```

3. **Adjust identna Resolution**
   ```python
   # Reduce resolution for speed
   result = client.fit_transform(
       df,
       identna_resolution=50,  # Reduce from default 100
       identna_effective_radius=0.15
   )
   ```

### Memory Shortage Error

**Symptoms**: `MemoryError` or `Out of memory`

**Solutions**:

1. **Batch Processing**
   ```python
   # Split processing for large data
   chunk_size = 1000
   results = []
   
   for i in range(0, len(df), chunk_size):
       chunk = df[i:i+chunk_size]
       if i == 0:
           # Create base map with first chunk
           result = client.fit_transform(chunk)
       else:
           # Add remaining chunks
           result = client.addplot(chunk)
       results.append(result)
   ```

2. **Data Type Optimization**
   ```python
   # Reduce memory usage
   df_optimized = df.copy()
   
   # float64 → float32
   float_cols = df.select_dtypes(include=['float64']).columns
   df_optimized[float_cols] = df_optimized[float_cols].astype('float32')
   
   # int64 → int32
   int_cols = df.select_dtypes(include=['int64']).columns
   df_optimized[int_cols] = df_optimized[int_cols].astype('int32')
   ```

---

## API Call Errors

### Rate Limiting Error

**Symptoms**: `Rate limit exceeded` or `Too many requests`

**Solutions**:

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        print(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise e
            return None
        return wrapper
    return decorator

# Usage example
@retry_with_backoff(max_retries=3)
def safe_addplot(data):
    return client.addplot(data)
```

### Compatibility Error

**Symptoms**: `Cannot use DataFrame addplot with csvform basemap`

**Solutions**:

```python
# Check map creation method
map_list = client.list_map()
current_map = next(m for m in map_list if m['mapNo'] == client.mapNo)

# Use appropriate addplot method
if current_map.get('processMethod') == 'csvform':
    result = client.addplot_csvform("new_data.csv")
elif current_map.get('processMethod') == 'waveform':
    result = client.addplot_waveform(["new_audio.wav"])
else:
    result = client.addplot(dataframe)
```

---

## Frequently Asked Questions

### Q: Can multiple CSV files be processed at once?

**A**: Yes, specify multiple files as a list.

```python
# Multiple CSV simultaneous processing
result = client.fit_transform_csvform([
    "data1.csv",
    "data2.csv", 
    "data3.csv"
])
```

### Q: Want to save analysis results to file

**A**: Use Map Inspector functionality to generate partial CSV.

```python
# 1. Open Map Inspector with shareUrl
print(f"Map Inspector: {client.shareUrl}")

# 2. After ellipse area selection, right-click and select
# "Create a raw CSV File subset containing only the Plots in the Area"
# to generate CSV file
```

### Q: What are the criteria for abnormality scores?

**A**: Score interpretation guide:

```python
score = result['abnormalityScore']

if score < 0.1:
    level = "Normal"
elif score < 0.3:
    level = "Minor change"
elif score < 0.7:
    level = "Attention needed"
else:
    level = "Abnormal"

print(f"Abnormality level: {level} (Score: {score:.3f})")
```

### Q: Results change each time with same data

**A**: Fix `random_seed` to ensure reproducibility.

```python
# Reproducible results
result = client.fit_transform(
    df,
    random_seed=42  # Specify fixed value
)
```

### Q: Want to automatically process large numbers of files

**A**: Batch processing script example:

```python
import os
import json
from datetime import datetime

def batch_process_directory(directory_path, output_file="results.json"):
    results = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            try:
                file_path = os.path.join(directory_path, filename)
                result = client.fit_transform_csvform(file_path)
                
                results.append({
                    'filename': filename,
                    'mapNo': client.mapNo,
                    'shareUrl': client.shareUrl,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Processing complete: {filename}")
                
            except Exception as e:
                print(f"❌ Error {filename}: {e}")
                results.append({
                    'filename': filename,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    # Save results to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

# Usage example
results = batch_process_directory("data_directory/")
```

---

## Support

### Log Collection

When reporting issues, please include the following information:

```python
import sys
import platform
import toorpia

# System information
print("=== System Information ===")
print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"toorPIA Version: {toorpia.__version__}")

# Error details when error occurs
try:
    result = client.problematic_operation()
except Exception as e:
    print(f"=== Error Details ===")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    
    # Stack trace
    import traceback
    print("=== Stack Trace ===")
    traceback.print_exc()
```

### Community Support

- [GitHub Issues](https://github.com/toorpia/toorpia/issues) - Bug reports and feature requests
- [Documentation](../README.md) - Latest information and updates

### Related Documentation

- [API Reference](api-reference.md) - Detailed API specifications
- [Map Inspector Guide](map-inspector.md) - GUI operation methods