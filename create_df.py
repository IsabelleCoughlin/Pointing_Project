import pandas as pd

column_names = ['Object Name', 'Peak X', 'Peak Y', 'Center X', 'Center Y', 'Offset X', 'Offset Y']

empty_df = pd.DataFrame(columns = column_names)
empty_df.to_csv('West-SBand.csv', index=False)
