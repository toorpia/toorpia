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
