import pandas as pd
column_names = ['Object Name', 'Peak X', 'Peak Y','Center X', 'Center Y', 'Offset X','Offset Y']
df = pd.DataFrame(columns=column_names)

df.to_csv('East-SBand.csv')