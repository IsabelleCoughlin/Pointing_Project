import pandas as pd

column_names = ['Object Name', 'Az (Rot)', 'El (Rot)', 'Az', 'El', 'Az Off (Rot)', 'El Off (Rot)']

empty_df = pd.DataFrame(columns = column_names)
empty_df.to_csv('Pulsars.csv', index=False)
