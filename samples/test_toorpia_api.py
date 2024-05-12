#!/usr/bin/env python
import pandas as pd

# create toorpia client
from toorpia import toorPIA
toorpia_client = toorPIA()  # defaults to getting the key using os.environ.get("TOORPIA_API_KEY")
# if you saved the key under a different environment variable name, you can also use the following way: 
# toorpia_client = toorPIA(api_key=os.environ.get("YOUR_VALID_KEY"))
 
df =  pd.read_csv("biopsy.csv") # read the data and store it in a pandas dataframe
df = df.drop(columns=["No", "ID", "Diagnosis"])  # drop the columns that are not needed

res = toorpia_client.fit_transform(df)  # make basemap and return the results

df_add =  pd.read_csv("biopsy-add.csv") # read the data and store it in a pandas dataframe
df_add = df_add.drop(columns=["No", "ID", "Diagnosis"])  # drop the columns that are not needed

res_add = toorpia_client.addplot(df_add)  # add the new data to the basemap and return the results
print(res_add)

maps = toorpia_client.list_map()
print(maps)
