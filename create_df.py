import pandas as pd

column_names = ['Time', 'Target Az', 'Target El', 'Rotor_Az', 'Rotor_El']

empty_df = pd.DataFrame(columns = column_names)
empty_df.to_csv('DFM_Data.csv', index=False)
