# toorpia api client

## How to install

```bash
pip install git+https://github.com/toorpia/toorpia.git
```

## How to Use

### Example: Client program

```python
#!/usr/bin/env python
import pandas as pd
import os

# create toorpia client
from toorpia import toorPIA
toorpia_client = toorPIA()  # defaults to getting the key using os.environ.get("TOORPIA_API_KEY")
# if you saved the key under a different environment variable name, you can also use the following way: 
# toorpia_client = toorPIA(api_key=os.environ.get("YOUR_VALID_KEY"))

# do the analysis
df = pd.read_csv("input.csv") # read csv file and store it in a pandas dataframe or a numpy array
results = toorpia_client.fit_transform(df)  # make basemap

# Add plot using a directory containing map data
df_add = pd.read_csv("add.csv")
results_add = toorpia_client.addplot(df_add, mapDataDir="/path/to/map/data/directory")

# Export the map
map_no = toorpia_client.mapNo
toorpia_client.export_map(map_no, "/path/to/export/directory")

# Import the map
new_map_no = toorpia_client.import_map("/path/to/import/directory")
```

### Environment Variable Configuration

#### API Key Configuration
To use the toorPIA API client, a valid API key is required. This key can be set via the environment variable TOORPIA_API_KEY. By setting the API key, you are authenticated to access the API as a registered user.

- For Unix/Linux/macOS:
  export TOORPIA_API_KEY='your-valid-api-key'

- For Windows:
  set TOORPIA_API_KEY=your-valid-api-key

#### API Server URL Configuration
For on-premise users, the toorPIA API client can be customized to connect to an internal server typically via HTTP, using an IP address, and served on port 3000. Ensure the URL does not include the path "api" as the backend does not use this in its routing.

- For Unix/Linux/macOS:
  export TOORPIA_API_URL='http://your-ip-address:3000'

- For Windows:
  set TOORPIA_API_URL=http://your-ip-address:3000

Once the API key and API server URL are properly set, these configurations will be utilized when accessing the API through the toorPIA client library.

### New Features: Map Export and Import

The toorPIA client now supports exporting and importing maps. These features allow you to save your maps for later use or transfer them between different instances of toorPIA.

#### Exporting a Map

To export a map, use the `export_map` method:

```python
toorpia_client.export_map(map_no, "/path/to/export/directory")
```

- `map_no`: The number of the map you want to export.
- `/path/to/export/directory`: The directory where the map files will be saved.

The method exports the map data as multiple files in the specified directory, preserving the original file names and formats.

#### Importing a Map

To import a previously exported map, use the `import_map` method:

```python
new_map_no = toorpia_client.import_map("/path/to/import/directory")
```

- `/path/to/import/directory`: The directory containing the map files to be imported.

The method reads all files from the specified directory and imports them as a new map. It returns the new map number assigned to the imported map.

#### Adding Plot with Map Data

The `addplot` method now supports using map data from a directory:

```python
results_add = toorpia_client.addplot(data, mapDataDir="/path/to/map/data/directory")
```

- `data`: The data to be added to the plot.
- `mapDataDir`: The directory containing the map data files.

This method reads all files from the specified directory and uses them as map data for the addplot operation.

These new features allow for easier backup, sharing, and transfer of map data between different toorPIA instances or sessions. They also provide more flexibility in handling map data composed of multiple files in various formats.
