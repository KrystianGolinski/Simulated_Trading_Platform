
# Shared utilities for data processing scripts

import pandas as pd

def get_date_column(df: pd.DataFrame) -> str:
    # Get the appropriate date column name (date or datetime)
    
    return 'date' if 'date' in df.columns else 'datetime'

def is_intraday_data(df: pd.DataFrame) -> bool:
    # Determine if data is intraday based on time component
    
    date_col = get_date_column(df)
    sample_date = pd.to_datetime(df[date_col].iloc[0])
    return sample_date.hour != 0 or sample_date.minute != 0 or sample_date.second != 0