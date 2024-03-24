# api

## toorPIA API利用イメージ

```python
toorPIA API利用イメージ
import pandas as pd
import matplotlib.pyplot as plt
 
# toorpiaのapi clientインスタンスの生成 
from toorpia import toorPIA
toorpia_client = toorPIA()  # defaults to getting the key using os.environ.get("TOORPIA_API_KEY")
# if you saved the key under a different environment variable name, you can also use the following way: 
# toorpia_client = toorPIA(api_key=os.environ.get("YOUR_VALID_KEY"))
 
# 解析実行
df =  pd.read_csv("input.csv") # 解析対象データはPandas DataFrameかNumPy Array形式として与える
results = toorpia_client.fit_transform(df)  # toorpiaによる解析処理を実行。この処理はサーバー側で実行されて結果がクライアントに返る
 
# 返り値はmatplotlibなどを使って活用可能
plt.scatter(results[:, 0], results[:, 1])
plt.show() 
```
