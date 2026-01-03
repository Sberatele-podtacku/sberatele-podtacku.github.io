import pandas as pd
df = pd.read_json('metadata.json')
df.to_csv('output.csv', index=False)