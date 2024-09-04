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
results = toorpia_client.fit_transform(df)
```

#### 2. Adding Data to an Existing Map

```python
df_add = pd.read_csv("add.csv")

# Using the most recent map
results_add = toorpia_client.addplot(df_add)

# Using a specific map number
results_add = toorpia_client.addplot(df_add, 123)

# Using a map from a directory
results_add = toorpia_client.addplot(df_add, "/path/to/basemap/data/directory")
```

#### 3. Listing Available Maps

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

## Error Handling

The client provides informative error messages for various scenarios, including authentication failures, invalid requests, and server errors. Always check the return values and handle potential errors in your code.

## Performance Considerations

- Map exports may take some time, especially for large datasets.
- For `addplot` operations, consider performance implications when working with large map data directories.

For more detailed information about specific methods and their parameters, refer to the inline documentation in the source code.
