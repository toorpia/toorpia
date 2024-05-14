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
 
# create toorpia client
from toorpia import toorPIA
toorpia_client = toorPIA()  # defaults to getting the key using os.environ.get("TOORPIA_API_KEY")
# if you saved the key under a different environment variable name, you can also use the following way: 
# toorpia_client = toorPIA(api_key=os.environ.get("YOUR_VALID_KEY"))
 
# do the analysis
df =  pd.read_csv("input.csv") # read csv file and store it in a pandas dataframe or a numpy array
results = toorpia_client.fit_transform(df)  # make basemap

df_add =  pd.read_csv("add.csv") 
results_add = toorpia_client.addplot(df_add)  # do addplot on the basemap
 
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
